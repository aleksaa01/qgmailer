from channels.event_channels import EmailEventChannel
from logs.loggers import default_logger, TESTING
from services.errors import get_error_code
from googleapis.gmail.labels import LABEL_ID_TRASH
from googleapis.gmail.history import HistoryRecord

LOG = default_logger()


class SyncHelper(object):
    def __init__(self):
        self._event_queue = []
        # unique local ID counter, used internally for synchronization purposes
        # If you have to sync data with the external API, then add 'ulid' field 
        # to every item in self._data
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


class Singleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, *kwargs)
        return cls._instance


class EmailSynchronizer(metaclass=Singleton):

    def __init__(self):
        self.registered_models = {}
        self.last_history_id = None
        EmailEventChannel.subscribe('synced', self.dispatch_updates)

    def register(self, model, label_id):
        self.registered_models[label_id] = model

    def send_sync_request(self, max_results=10):
        print("In send_sync_request")
        if self.last_history_id is None:
            last_hid = 0
            for model in self.registered_models.values():
                first_item = model.get_item(0)
                total_items = model.total_items()
                if (total_items == -1 and first_item is None) or \
                        (total_items > 0 and first_item is None):
                    # Model didn't receive any data yet, so skip this sync request.
                    print("Models data is not fetched yet, skipping sync request...")
                    return
                elif total_items == 0:
                    # This model is empty, skip to the next one.
                    continue
                hid = int(first_item.get('historyId'))
                last_hid = max(hid, last_hid)
            self.last_history_id = last_hid

        print("Last history id: ", self.last_history_id)
        EmailEventChannel.publish(
            'short_sync', start_history_id=str(self.last_history_id), max_results=max_results)

    def dispatch_updates(self, history_records, last_history_id, error=''):
        if error:
            parsed_error = get_error_code(error)
            if parsed_error == 404:
                # TODO: Partial sync failed, do full sync.
                LOG.error(f"Partial sync failed. Error: {error}.")
                return
        try:
            self._dispatch_updates(history_records, last_history_id)
        except Exception as err:
            LOG.error(f"Failed to dispatch history_records. Error: {err}")
            if TESTING is True:
                raise err

    def _dispatch_updates(self, history_records, last_history_id):
        self.last_history_id = last_history_id
        print("Number of history records:", len(history_records))
        print('-------- DISPATCHING HISTORY RECORDS --------')
        for his_record in history_records:
            model = self.registered_models.get(his_record.initial_label_id)
            action = his_record.action
            if action == HistoryRecord.ACTION_ADD:
                email = his_record.email
                if model.find_email(email.get('id'), email.get('internalDate')) == -1:
                    model.insert_email(email)
                    print(f"Inserted email with id={email.get('id')} into the "
                          f"model with label_id={his_record.initial_label_id}")
                else:
                    print(f"Email with id={email.get('id')} is already present "
                          f"in the model with label_id={his_record.initial_label_id}")
            elif action == HistoryRecord.ACTION_DELETE:
                if model.pop_email(his_record.message_id):
                    print(f"Deleted email with id={his_record.message_id} from "
                          f"the model with label_id={his_record.initial_label_id}")
                else:
                    print(f"Email with id={his_record.message_id} was already deleted "
                          f"from the model with label_id={his_record.initial_label_id}")
            elif action == HistoryRecord.ACTION_TRASH:
                trash_model = self.registered_models.get(LABEL_ID_TRASH)
                email = his_record.email
                model.pop_email(email.get('id'))
                trashed_idx = trash_model.find_email(email.get('id'), email.get('internalDate'))
                if trashed_idx != -1:
                    # This means that our app made this change, thereby we just have to
                    # update the historyId.
                    trash_model.get_item(trashed_idx)['historyId'] = his_record.history_id
                    print(f"Email with id={email.get('id')} was already moved to trash from the "
                          f"model with label_id={his_record.initial_label_id}. "
                          f"Updating only historyId({his_record.history_id}).")
                else:
                    trash_model.insert_email(email)
                    print(f"Email moved to the trash model from the model with "
                          f"label_id={his_record.initial_label_id}.")
            elif action == HistoryRecord.ACTION_RESTORE:
                trash_model = self.registered_models.get(LABEL_ID_TRASH)
                email = his_record.email
                trash_model.pop_email(email.get('id'))
                restored_idx = model.find_email(email.get('id'), email.get('internalDate'))
                if restored_idx != -1:
                    model.get_item(restored_idx)['historyId'] = his_record.history_id
                    print(f"Email with id={email.get('id')} was already restored from the trash to "
                          f"the model with label_id={his_record.initial_label_id}. "
                          f"Updating only historyId({his_record.history_id}).")
                else:
                    model.insert_email(email)
                    print(f"Email moved from the trash model to "
                          f"the model with label_id={his_record.initial_label_id}.")
            else:
                raise ValueError(f"Unknown history record action: {action}")
        print('-------- HISTORY RECORDS DISPATCHED --------')

    @classmethod
    def get_instance(cls):
        if cls._instance:
            return cls._instance
        instance = cls()
        return instance
