from googleapis.gmail.labels import GMAIL_LABEL_TRASH
from googleapis.gmail.history import HistoryRecord
from channels.event_channels import EmailEventChannel
from logs.loggers import default_logger, TESTING
from services.errors import get_error_code
from services.utils import email_message_to_dict

import time


LOG = default_logger()


class SyncHelper(object):
    def __init__(self):
        self._event_queue = []
        # unique local ID counter, used internally for synchronization purposes
        # If you have to sync data with the external API, then add 'ulid' field 
        # to every item in self._data
        # This is primarily used by the ContactModel because user can execute multiple actions in a
        # very short amount of time, and thus you need something like this so you can handle any
        # errors or successful operations in a sane manner.
        self.ulid_counter = 0

    def new_ulid(self):
        """Returns a new unique local ID that's used internally for synchronization purposes."""
        ulid = self.ulid_counter
        self.ulid_counter += 1
        return ulid

    def push_event(self, event_channel, topic, payload, item):
        if len(self._event_queue) == 0:
            event_channel.publish(topic, **payload)
        self._event_queue.append((event_channel, topic, payload, item))
    
    def pull_event(self):
        return self._event_queue.pop(0)
    
    def push_next_event(self):
        if len(self._event_queue) > 0:
            event_channel, topic, payload, item = self._event_queue[0]
            event_channel.publish(topic, **payload)
            return event_channel, topic, payload, item

    def peek_event(self):
        if len(self._event_queue):
            return self._event_queue[0]

    def events(self):
        return self._event_queue

    def remove_event(self, idx):
        self._event_queue.pop(idx)

    def __len__(self):
        return len(self._event_queue)


class Singleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, *kwargs)
        return cls._instance


# TODO: Fix this one
class EmailSynchronizer(metaclass=Singleton):

    def __init__(self):
        self.registered_models = {}
        self.last_history_id = None
        EmailEventChannel.subscribe('synced', self.dispatch_updates)

    def register(self, model, label_id):
        self.registered_models[label_id] = model

    def send_sync_request(self):
        LOG.debug("Sending a short_sync event.")
        EmailEventChannel.publish('short_sync')

    def dispatch_updates(self, history_records, error=''):
        if error:
            parsed_error = get_error_code(error)
            if parsed_error == 404:
                # TODO: Partial sync failed, do full sync. Don't forget to wrap short_sync
                #  api call in try-except block.
                LOG.error(f"Partial sync failed. Error: {error}.")
                return
        try:
            self._dispatch_updates(history_records)
        except Exception as err:
            # TODO: Reset all models. And run full sync.
            LOG.error(f"Failed to dispatch history_records. Error: {err}")
            if TESTING is True:
                raise err

    def _dispatch_updates(self, history_records):
        LOG.debug("Number of history records:", len(history_records))
        LOG.info('-------- DISPATCHING HISTORY RECORDS --------')
        LOG.debug(f"History records: {history_records.values()}")
        t1 = time.perf_counter()
        for his in history_records.values():
            LOG.debug("--- new history record ---")
            # For every history record there are 3 possibilities:
            # 1.) We were responsible for that
            # 2.) Someone else is responsible for that
            # 3.) Both? I think Gmail-API tries to squeeze multiple changes into one record.
            m = his.message
            parsed_email_message = email_message_to_dict(m)
            if his.has_type(HistoryRecord.MESSAGE_DELETED):
                LOG.debug("In HistoryRecord.MESSAGE_DELETED")
                label_ids = m.label_ids.split(',')
                LOG.debug(f"label_ids: {label_ids}")
                if GMAIL_LABEL_TRASH in label_ids:
                    LOG.debug("TRASH is present in label_ids")
                    trash_model = self._get_model(GMAIL_LABEL_TRASH)
                    idx = trash_model.find_email(m.message_id, m.internal_date)
                    if idx != -1:
                        trash_model.pop_email(m.message_id, idx)
                else:
                    LOG.debug("TRASH is NOT present in label_ids")
                    for lid in label_ids:
                        model = self._get_model(lid)
                        if not model:
                            continue
                        idx = model.find_email(m.message_id, m.internal_date)
                        if idx != -1:
                            model.pop_email(m.message_id, idx)
            elif his.has_type(HistoryRecord.MESSAGE_ADDED):
                LOG.debug("In HistoryRecord.MESSAGE_ADDED")
                if his.has_type(HistoryRecord.LABELS_REMOVED):
                    # Remove message from all 'removed labels'(can be thought of as 'old labels')
                    LOG.debug(f"labels_removed: {his.labels_removed}")
                    for lbl in his.labels_removed:
                        model = self._get_model(lbl)
                        if not model:
                            continue
                        idx = model.find_email(m.message_id, m.internal_date)
                        if idx != -1:
                            model.pop_email(m.message_id, idx)
                label_ids = m.label_ids.split(',')
                LOG.debug(f"label_ids: {label_ids}")
                if GMAIL_LABEL_TRASH in label_ids:
                    LOG.debug("TRASH is present in label_ids")
                    # If message was added and it contains TRASH label, then we have to add it to
                    # trash model.
                    trash_model = self._get_model(GMAIL_LABEL_TRASH)
                    if trash_model.find_email(m.message_id, m.internal_date) == -1:
                        trash_model.insert_email(parsed_email_message)
                    label_ids.remove(GMAIL_LABEL_TRASH)
                    # And we have to make sure that it is not present in any other model
                    for lbl in label_ids:
                        model = self._get_model(lbl)
                        if not model:
                            continue
                        idx = model.find_email(m.message_id, m.internal_date)
                        if idx != -1:
                            model.pop_email(m.message_id, idx)
                else:
                    LOG.debug("TRASH is NOT present in label_ids")
                    # If TRASH is not in label_ids, then we can add the message to all matching
                    # models, if it's not already there.
                    for lbl in label_ids:
                        model = self._get_model(lbl)
                        if not model:
                            continue
                        if model.find_email(m.message_id, m.internal_date) == -1:
                            model.insert_email(parsed_email_message)
            # This should strictly process history records with only LABELS_ADDED and
            # LABELS_REMOVED record types.
            elif his.labels_modified():
                LOG.debug("In HistoryRecord.labels_modified()")
                # Remove message from all old places.
                LOG.debug(f"labels_removed: {his.labels_removed}")
                for lbl in his.labels_removed:
                    model = self._get_model(lbl)
                    if not model:
                        continue
                    idx = model.find_email(m.message_id, m.internal_date)
                    if idx != -1:
                        model.pop_email(m.message_id, idx)

                label_ids = m.label_ids.split(',')
                LOG.debug(f"label_ids: {label_ids}")
                if GMAIL_LABEL_TRASH in label_ids:
                    LOG.debug("TRASH is present in label_ids")
                    # If message contains TRASH label, then we have to add it to trash model.
                    trash_model = self._get_model(GMAIL_LABEL_TRASH)
                    if trash_model.find_email(m.message_id, m.internal_date) == -1:
                        trash_model.insert_email(parsed_email_message)
                    label_ids.remove(GMAIL_LABEL_TRASH)
                    # And we have to make sure that it is not present in any other model
                    for lbl in label_ids:
                        model = self._get_model(lbl)
                        if not model:
                            continue
                        idx = model.find_email(m.message_id, m.internal_date)
                        if idx != -1:
                            model.pop_email(m.message_id, idx)
                else:
                    LOG.debug("TRASH is NOT present in label_ids")
                    # If TRASH is not in label_ids, then we have 2 cases(because we know we already
                    # have a record of it, otherwise we would end up in MESSAGE_ADDED):
                    # 1.) If TRASH was removed from labels(aka. is in labels_removed), then we have
                    # to add that message to all labels
                    # 2.) Otherwise, we only have to add that message to labels in labels_added
                    LOG.debug(f"labels_removed: {his.labels_removed}")
                    if GMAIL_LABEL_TRASH in his.labels_removed:
                        for lbl in label_ids:
                            model = self._get_model(lbl)
                            if not model:
                                continue
                            if model.find_email(m.message_id, m.internal_date) == -1:
                                model.insert_email(parsed_email_message)
                    else:
                        LOG.debug(f"labels_added: {his.labels_added}")
                        for lbl in his.labels_added:
                            model = self._get_model(lbl)
                            if not model:
                                continue
                            if model.find_email(m.message_id, m.internal_date) == -1:
                                model.insert_email(parsed_email_message)

        for model in self.registered_models.values():
            model.check_loaded_data()

        t2 = time.perf_counter()
        LOG.debug(f"HISTORY RECORDS DISPATCH PERF: {t2 - t1}")
        LOG.info('-------- HISTORY RECORDS DISPATCHED --------')

    def _get_model(self, label_id):
        """History records may contain unknown Label IDs, this method takes care of errors."""
        # TODO: If we fail to get a matching model, it might mean that our labels are
        #  out of sync, thus we have to schedule a lebels_sync and reset the cache
        #  of every model.
        model = self.registered_models.get(label_id)
        if model is None:
            LOG.warning(f"Missing model for Label ID = {label_id}.")
        return model

    @classmethod
    def get_instance(cls):
        if cls._instance:
            return cls._instance
        instance = cls()
        return instance
