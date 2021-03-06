
class Topic(object):

    def __init__(self, **kwargs):
        self.subscribers = []
        self.kwargs = kwargs

    def subscribe(self, callback):
        self.subscribers.append(callback)

    def publish(self, **kwargs):
        self._validate_kwargs(**kwargs)
        for sub in self.subscribers:
            sub(**kwargs)

    def _validate_kwargs(self, **kwargs):
        """
        Keyword arguments are valid only if every required argument is present and is of the required type.
        In order to enable error reports, any other field should be ignored.
        """
        for kwarg_name, val_type in self.kwargs.items():
            value = kwargs.get(kwarg_name, None)
            if value is None:
                raise KeyError(f"Keyword agument '{kwarg_name}' is missing.")
            if isinstance(value, val_type) is False:
                raise TypeError(
                    f"Keyword argument '{kwarg_name}' has the wrong type. Expected {val_type}, but got {type(value)} instead.")
        return True


class EventChannel(object):
    topic_map = {}

    @classmethod
    def subscribe(self, topic, callback):
        topic_obj = self.topic_map.get(topic)
        if topic_obj is None:
            raise ValueError(f'Topic "{topic}" doesn\'t exist.')
        topic_obj.subscribe(callback)

    @classmethod
    def publish(self, topic, **kwargs):
        topic_obj = self.topic_map.get(topic)
        if topic_obj is None:
            raise ValueError(f'Topic "{topic}" doesn\'t exist.')

        topic_obj.publish(**kwargs)


class EmailEventChannel(EventChannel):
    topic_map = {
        'email_request': Topic(email_id=str),
        'email_response': Topic(body=str, attachments=list),
        'page_request': Topic(label_id=int, max_results=int),
        'page_response': Topic(label_id=int, emails=list),
        'send_email': Topic(label_id=int, email_msg=dict),
        'email_sent': Topic(label_id=int, email=dict),
        'trash_email': Topic(email=dict, from_lbl_id=int, to_lbl_id=int),
        'email_trashed': Topic(email=dict, from_lbl_id=int, to_lbl_id=int),
        'restore_email': Topic(email=dict, from_lbl_id=int, to_lbl_id=int),
        'email_restored': Topic(email=dict, from_lbl_id=int, to_lbl_id=int),
        'delete_email': Topic(label_id=int, id=str),
        'email_deleted': Topic(label_id=int),
        'short_sync': Topic(start_history_id=str, max_results=int),
        'synced': Topic(history_records=list, last_history_id=str),
        'get_total_messages': Topic(label_id=int),
        'total_messages': Topic(label_id=int, num_messages=int),
        'modify_labels': Topic(email_id=str, to_add=tuple, to_remove=tuple),
        'labels_modified': Topic(),
    }


class ContactEventChannel(EventChannel):
    topic_map = {
        'page_request': Topic(max_results=int),
        'page_response': Topic(contacts=list, total_contacts=int),
        'pick_contact': Topic(),
        'contact_picked': Topic(email=str),
        'remove_contact': Topic(resourceName=str),
        'contact_removed': Topic(),
        'add_contact': Topic(name=str, email=str),
        'contact_added': Topic(name=str, email=str, resourceName=str, etag=str),
        'edit_contact': Topic(name=str, email=str, contact=dict),
        'contact_edited': Topic(name=str, email=str, resourceName=str, etag=str),
    }


class OptionEventChannel(EventChannel):
    topic_map = {
        'emails_per_page': Topic(page_length=int),
        'contacts_per_page': Topic(page_length=int),
        'font_size': Topic(font_size=int),
        'theme': Topic(theme=str),
        'inbox_shortcut': Topic(inbox_shortcut=str),
        'send_email_shortcut': Topic(send_email_shortcut=str),
        'sent_shortcut': Topic(sent_shortcut=str),
        'contacts_shortcut': Topic(contacts_shortcut=str),
        'trash_shortcut': Topic(trash_shortcut=str),
        'options_shortcut': Topic(options_shortcut=str),
    }


class ShortcutEventChannel(EventChannel):
    topic_map = {
        'inbox_shortcut': Topic(),
        'send_email_shortcut': Topic(),
        'sent_shortcut': Topic(),
        'contacts_shortcut': Topic(),
        'trash_shortcut': Topic(),
        'options_shortcut': Topic(),
    }


class ProcessEventChannel(EventChannel):
    topic_map = {
        'commands': Topic(flag=int),
    }
