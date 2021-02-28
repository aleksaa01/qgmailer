from channels.event_channels import EmailEventChannel
from logs.loggers import default_logger
from services.errors import get_error_code

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

    def dispatch_updates(self, events, last_history_id, error=''):
        if error:
            parsed_error = get_error_code(error)
            if parsed_error == 404:
                # TODO: Partial sync failed, do full sync.
                LOG.error(f"Partial sync failed. Error: {error}.")
                return
        try:
            self._dispatch_updates(events, last_history_id)
        except Exception as err:
            LOG.error(f"Failed to dispatch events. Error: {err}")

    def _dispatch_updates(self, events, last_history_id):
        self.last_history_id = last_history_id
        print("Number of events:", len(events))
        print('--------', 'DISPATCHING EVENTS', '--------')
        for event in events:
            action = event['action']
            if action == 'email_added':
                to_label_id = event['to_lbl_id']
                email = event['email']
                model = self.registered_models.get(to_label_id)
                # We check if email already exists(just for sent email)
                if model.find_email(email.get('id'), email.get('internalDate')) == -1:
                    model.insert_email(email)
                    print(f"Email with id={email.get('id')} inserted into {to_label_id} model.")
                else:
                    print(f"Email not inserted in {to_label_id} emails. Email snippet:", email.get('snippet'))
            elif action == 'email_deleted':
                from_label_id = event['from_lbl_id']
                email_id = event['id']
                # To delete an email we don't really need the historyId, only label_id and id.
                model = self.registered_models.get(from_label_id)
                model.pop_email(email_id)
                print(f"Email with id={email_id} removed from {from_label_id} model.")
            elif action == 'email_trashed':
                from_label_id = event['from_lbl_id']
                trash_model = self.registered_models.get('trash')
                model = self.registered_models.get(from_label_id)
                email = model.pop_email(event['id'])
                if (email is not None) and trash_model.find_email(email.get('id'), email.get('internalDate')) == -1:
                    email['historyId'] = event['historyId']
                    trash_model.insert_email(email)
                    print(f"Email removed from {from_label_id} model and added into trash model.")
                else:
                    # This event might be from our app, or the email was deleted in the meantime.
                    print("Email not inserted in trashed emails. Email: ", email)
            elif action == 'email_restored':
                to_label_id = event['to_lbl_id']
                email_id = event['id']
                
                trash_model = self.registered_models.get('trash')
                model = self.registered_models.get(to_label_id)
                email = trash_model.pop_email(email_id)
                if (email is not None) and model.find_email(email.get('id'), email.get('internalDate')) == -1:
                    email['historyId'] = event['historyId']
                    model.insert_email(email)
                    print(f"Email removed from trash model and added into {to_label_id} model.")
                else:
                    # This event might be from our app, or the email was already deleted.
                    print(f"Email not inserted in {to_label_id} emails. Email: {email}")
                    pass
            else:
                raise ValueError(f"Unknown event action: {action}.")
        print('--------', 'EVENTS DISPATCHED', '--------')

    @classmethod
    def get_instance(cls):
        if cls._instance:
            return cls._instance
        instance = cls()
        return instance
