from PyQt5.QtCore import Qt

from qmodels.base import BaseListModel
from qmodels.options import options
from channels.event_channels import EmailEventChannel, OptionEventChannel
from channels.signal_channels import SignalChannel
from services.sync import SyncHelper, EmailSynchronizer
from logs.loggers import default_logger
from services.errors import get_error_code
from googleapis.gmail.labels import GMAIL_LABEL_UNREAD, GMAIL_LABEL_TRASH

LOG = default_logger()
EmailRole = Qt.UserRole + 100


class EmailModel(BaseListModel):

    on_error = SignalChannel(str, str)

    def __init__(self, label_id, request_callback_delay, data=None):
        super().__init__(data)

        self.page_length = options.emails_per_page
        self.label_id = label_id
        self.delay_request = request_callback_delay

        EmailEventChannel.subscribe('email_list_response', self.add_new_page)
        EmailEventChannel.subscribe('email_trashed', self.handle_email_trashed)
        EmailEventChannel.subscribe('email_restored', self.handle_email_restored)
        EmailEventChannel.subscribe('email_deleted', self.handle_email_deleted)
        EmailEventChannel.subscribe('email_sent', self.handle_email_sent)
        OptionEventChannel.subscribe('emails_per_page', self.change_page_length)

        self.sync_helper = SyncHelper()
        # Register this model to synchronizer in order to be able to receive short sync updates.
        EmailSynchronizer.get_instance().register(self, label_id)

        limit = self.page_length
        offset = len(self)
        self.sync_helper.push_event(
            EmailEventChannel, 'email_list_request',
            {'label_id': self.label_id, 'limit': limit, 'offset': offset}, None
        )

        self._backoff = 1
        # fully_loaded just means that database is done with full syncing.
        self.fully_loaded = False
        # _load_next_page indicates whether or not we should load the next page, mostly
        # used by add_new_page method when processing new data.
        self._load_next_page = False

    def data(self, index, role=Qt.DisplayRole):
        if role == EmailRole:
            return self._displayed_data[index.row()]
        elif role == Qt.ToolTipRole:
            return str(self._displayed_data[index.row()])

    def current_index(self):
        return self.begin, self.end

    def add_new_page(self, label_id, limit, emails, fully_synced, error=''):
        # FIXME: Think about implications of changing page length, while some already sent request
        #  is still being processed. What should I do in that situation ?
        if label_id != self.label_id:
            return

        if error:
            LOG.error(f"Page request failed... Error: {error}")
            self.on_error.emit(self.label_id, "Failed to load next page.")
            self.sync_helper.pull_event()
            self.sync_helper.push_next_event()
            return

        if self.end - self.begin < self.page_length:
            # User is currently at the last page, so we have to reset the views.
            notify = True
        else:
            notify = False

        # We need this amount of checking because we might be in the process of full sync.
        # Which means we can't be sure if there is more data to be found outside the database, and that's
        # also why we need exponential back-off.
        if len(emails) == self.page_length:
            # We don't care if fully_synced is True or not, we got our full response back.
            # Done
            self._backoff = 1
            self.add_data(emails, notify=notify)
        elif len(emails) < self.page_length:
            if fully_synced is False:
                if limit < self.page_length and limit - len(emails) == 0:
                    # We got back FULL PARTIAL response
                    # Done
                    # Btw you can't know if previous partial request was empty(0 emails), so you have
                    # to use calculated notify based on self.end
                    # This path will also get triggered if we send an 'email_list_request' after sending
                    # an email to trash.
                    self._backoff = 1
                    self.add_data(emails, notify=notify)
                elif limit < self.page_length:
                    LOG.warning(f"EmailModel.add_new_page >>> Sending a partial request after partial, backoff: {self._backoff}")
                    # Previous request was partial
                    new_limit = limit - len(emails)
                    # emails from previous partial response were already added
                    new_offset = len(self) + len(emails)
                    callback = lambda: self.sync_helper.push_event(
                        EmailEventChannel, 'email_list_request',
                        {'label_id': self.label_id, 'limit': new_limit, 'offset': new_offset}, None
                    )
                    self.delay_request(callback, self._backoff)
                    self._backoff = min(self._backoff * 2, 16)
                    self.add_data(emails, notify=notify)
                else:
                    LOG.warning(f"EmailModel.add_new_page >>> Sending a full/partial request after full/partial, backoff: {self._backoff}")
                    # Previous request was full, now we are either going to send a full request if
                    # len(emails) == 0, or partial if len(emails) > 0
                    new_limit = self.page_length - len(emails)
                    new_offset = len(self) + len(emails)
                    callback = lambda: self.sync_helper.push_event(
                        EmailEventChannel, 'email_list_request',
                        {'label_id': self.label_id, 'limit': new_limit, 'offset': new_offset}, None
                    )
                    self.delay_request(callback, self._backoff)
                    self._backoff = min(self._backoff * 2, 16)
                    self.add_data(emails, notify=notify)
            else:
                # fully_synced is True, we know there is no more data.
                # Done
                self._backoff = 1
                if limit < self.page_length:
                    # Previous request was partial
                    self.add_data(emails, notify=notify)
                else:
                    # Previous request was full
                    self.add_data(emails, notify=notify)
                # If we are fully synced -> pop an email -> request 1 email -> get 1 email back
                # ^ In this case we are going to hit this branch, but that doesn't mean we are fully
                # loaded. Thus we can only be fully loaded if:
                # fully_synced is True AND len(emails) < limit
                if len(emails) < limit:
                    self.fully_loaded = True

        if self._load_next_page:
            self.load_next()

        # Make sure to pull the event that resulted in this response first, before calling
        # _maybe_load_more_data which might send another one.
        self.sync_helper.pull_event()
        self.sync_helper.push_next_event()
        # We might've removed an email while waiting for response, so check if more data is needed.
        self._maybe_load_more_data()

    def insert_email(self, email):
        # Implement binary search and insert the email in last_element_index + 0/1,
        # depending on the value of internalDate of that last element.
        email_intd = int(email.get('internal_date'))
        start = 0
        end = len(self._data)
        while start < end:
            # integer overflow is not a problem in Python, so no need for "(end - start) // 2 + start"
            mid = (start + end) // 2
            intd = int(self._data[mid].get('internal_date'))
            if email_intd > intd:
                end = mid
            else:
                start = mid + 1

        # Last item checked is now stored in start
        self._data.insert(start, email)

        self.end = min(self.begin + self.page_length, len(self._data))
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def remove_email(self, email_id, raise_if_missing=False):
        matching_email = None
        for idx, email in enumerate(self._data):
            if email.get('message_id') == email_id:
                matching_email = self._data.pop(idx)
                break
        # TODO: We should probably empty sync_helper's event queue as well.

        if matching_email is None:
            if raise_if_missing:
                raise ValueError(f"Email with id: {email_id} doesn't exist.")
            else:
                return None

        self.end = min(self.begin + self.page_length, len(self._data))
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

        return matching_email

    def pop_email(self, email_id, index, raise_if_missing=False):
        matching_email = None
        if self._data[index].get('message_id') == email_id:
            matching_email = self._data.pop(index)

        if matching_email is None:
            if raise_if_missing:
                raise ValueError(f"Email with id: {email_id} doesn't exist.")
            else:
                return None

        self.end = min(self.begin + self.page_length, len(self._data))
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

        return matching_email

    def find_email(self, email_id, internal_date=None):
        if internal_date is not None:
            start = 0
            end = len(self._data)
            while start < end:
                mid = (start + end) // 2
                email = self._data[mid]
                date = email.get('internal_date')
                # Emails are sorted in descending order, from biggest to lowest date.
                if internal_date > date:
                    end = mid
                elif internal_date < date:
                    start = mid + 1
                else:
                    assert email.get('message_id') == email_id
                    return mid
        else:
            for idx, email in enumerate(self._data):
                if email.get('message_id') == email_id:
                    return idx
        return -1

    def view_email(self, idx):
        email = self._displayed_data[idx]
        # Should we check labelIds here ?
        # In my opinion, there is no reason to do this, eventually we can even drop the use of labelIds.
        if email.get('unread') is True:
            email['unread'] = False
            EmailEventChannel.publish(
                'modify_labels', message_id=email.get('message_id'), all_labels=email.get('label_ids'),
                to_add=(), to_remove=(GMAIL_LABEL_UNREAD,)
            )
        EmailEventChannel.publish('email_request', message_id=email.get('message_id'))

    def change_page_length(self, page_length):
        self.set_page_length(page_length)

    def load_next_page(self):
        if not self.fully_loaded and self.end == len(self):
            self._load_next_page = True
            self.sync_helper.push_event(
                EmailEventChannel, 'email_list_request',
                {'label_id': self.label_id, 'limit': self.page_length, 'offset': len(self)}, None
            )
            return

        self.load_next()
        self._maybe_load_more_data()

    def load_next(self):
        super().load_next()
        self._load_next_page = False

    def load_previous_page(self):
        self.load_previous()

    def trash_email(self, idx):
        LOG.info(f"Moving email at index {idx} to trash: {self._displayed_data[idx].get('snippet')}")
        email = self._displayed_data[idx]
        topic = 'trash_email'
        payload = {'email': email, 'from_lbl_id': self.label_id, 'to_lbl_id': ''}
        self.sync_helper.push_event(EmailEventChannel, topic, payload, email)

        self._data.pop(self.begin + idx)
        self.end = min(self.begin + self.page_length, len(self._data))
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

        self._maybe_load_more_data()

    def handle_email_trashed(self, email, from_lbl_id, to_remove, error=''):
        if from_lbl_id != self.label_id and self.label_id not in to_remove and \
                self.label_id != GMAIL_LABEL_TRASH:
            return

        # Trying to move email to trash that was previously moved to trash won't produce an error.
        # But trying to move email to trash that was previously deleted will produce an error.
        if error:
            # In case we are in the EmailModel for trashed emails, then we just return
            # cause there was an error, and we don't have to fix nor store anything.
            if self.label_id != from_lbl_id:
                return
            error_code = get_error_code(error)
            if error_code == 404:
                LOG.warning("Failed to move email to trash, it was already deleted.")
                self.on_error.emit(self.label_id, "Can't move that email to trash because it was already deleted.")
            else:
                LOG.error(f"Failed to move the email to trash. Error: {error}")
                self.on_error.emit(self.label_id, "Failed to move the email to trash.")

            self.sync_helper.pull_event()
            self.sync_helper.push_next_event()
            return

        # Check if self.label_id == from_lbl_id first, because that label also exists in to_remove
        if from_lbl_id == self.label_id:
            # This is the inbox model, so now we can remove the event
            self.sync_helper.pull_event()
            LOG.info(f"Email sent to trash successfully(label_id): {self.label_id}")
            # Now send next event if there's any left in the queue
            self.sync_helper.push_next_event()
        elif self.label_id == GMAIL_LABEL_TRASH:
            # This is the trash model, so now we add it to model data
            self.insert_email(email)
        elif self.label_id in to_remove:
            self.remove_email(email.get('message_id'))
            self._maybe_load_more_data()

    def restore_email(self, idx):
        LOG.info(f"Restoring email at index {idx}: {self._displayed_data[idx].get('snippet')}")
        email = self._displayed_data[idx]
        topic = 'restore_email'
        payload = {'email': email}
        self.sync_helper.push_event(EmailEventChannel, topic, payload, email)

        self._data.pop(self.begin + idx)
        self.end = min(self.begin + self.page_length, len(self._data))
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def handle_email_restored(self, email, to_add, error=''):
        if self.label_id != GMAIL_LABEL_TRASH and self.label_id not in to_add:
            return

        # Trying to restore already restored email won't produce an error.
        # But trying to restore previously deleted email will produce an error.
        if error:
            if self.label_id != GMAIL_LABEL_TRASH:
                return
            error_code = get_error_code(error)
            if error_code == 404:
                LOG.warning("Failed to restore the email, it was already deleted.")
                self.on_error.emit(self.label_id, "Can't restore that email, because it was already deleted.")
            else:
                LOG.error(f"Failed to restore email. Error: {error}")
                self.on_error.emit(self.label_id, "Failed to restore the email.")

            self.sync_helper.pull_event()
            self.sync_helper.push_next_event()
            return

        if self.label_id == GMAIL_LABEL_TRASH:
            self.sync_helper.pull_event()
            LOG.info(f"Email completely restored(label_id: {self.label_id})")
            self.sync_helper.push_next_event()
        elif self.label_id in to_add:
            self.insert_email(email)

    def delete_email(self, idx):
        LOG.info(f"Deleting email at index {idx}: {self._displayed_data[idx].get('snippet')}")
        email = self._displayed_data[idx]
        topic = 'delete_email'
        payload = {'label_id': self.label_id, 'message_id': email.get('message_id')}
        self.sync_helper.push_event(EmailEventChannel, topic, payload, email)

        self._data.pop(self.begin + idx)
        self.end = min(self.begin + self.page_length, len(self._data))
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

        self._maybe_load_more_data()

    def handle_email_deleted(self, label_id, error=''):
        if label_id != self.label_id:
            return

        # Trying to delete previously restored email won't produce an error, email will be deleted.
        # But trying to delete previously deleted email will produce an error.
        if error:
            error_code = get_error_code(error)
            if error_code == 404:
                LOG.warning("Failed to delete the email, it was already deleted.")
                self.on_error.emit(self.label_id, "Can't delete that email, because it was already deleted.")
            else:
                LOG.error(f"Failed to delete email. Error: {error}")
                self.on_error.emit(self.label_id, "Failed to delete the email.")

            self.sync_helper.pull_event()
            self.sync_helper.push_next_event()
            return

        self.sync_helper.pull_event()
        LOG.info("Email completely deleted.")
        self.sync_helper.push_next_event()

    def handle_email_sent(self, label_id, email, error=''):
        if self.label_id != label_id:
            return

        # Sending email to non existing email address won't produce an error.
        # You will just get email back from "Mail Devlivery Subsystem" saying "Address not found".
        if error:
            self.on_error.emit(self.label_id, "An error occurred, email wasn't sent.")
            LOG.error(f"Failed to send the email. Error: {error}")
            return

        self.insert_email(email)

    def _maybe_load_more_data(self):
        LOG.warning("MAYBE LOAD MORE DATA !!!")
        if len(self.sync_helper) and not self.fully_loaded and self.end == len(self) and \
                self.end - self.begin < self.page_length:
            limit = self.page_length - (self.end - self.begin)
            self.sync_helper.push_event(
                EmailEventChannel, 'email_list_request',
                {'label_id': self.label_id, 'limit': limit, 'offset': len(self)}, None
            )

    def check_loaded_data(self):
        """
        Can be called by external systems, like partial synchronization system, after a series of
        actions(insert, pop, remove...) to check loaded data and send a request for more if necessary.
        """
        self._maybe_load_more_data()