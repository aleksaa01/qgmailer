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
                raise KeyError(f"Keyword argument '{kwarg_name}' is missing.")
            if isinstance(value, val_type) is False:
                raise TypeError(
                    f"Keyword argument '{kwarg_name}' has the wrong type. Expected {val_type}, but got {type(value)} instead.")
        return True


class EventChannel(object):
    topic_map = {}

    @classmethod
    def subscribe(cls, topic, callback):
        topic_obj = cls.topic_map.get(topic)
        if topic_obj is None:
            raise ValueError(f'Topic "{topic}" doesn\'t exist.')
        topic_obj.subscribe(callback)

    @classmethod
    def publish(cls, topic, **kwargs):
        topic_obj = cls.topic_map.get(topic)
        if topic_obj is None:
            raise ValueError(f'Topic "{topic}" doesn\'t exist.')

        topic_obj.publish(**kwargs)


class EmailEventChannel(EventChannel):
    topic_map = {
        'email_request': Topic(message_id=int),
        'email_response': Topic(body=str, attachments=list),
        'email_list_request': Topic(label_id=str, limit=int, offset=int),
        'email_list_response': Topic(label_id=str, limit=int, emails=list, fully_synced=bool),
        'send_email': Topic(email_msg=dict),
        'email_sent': Topic(label_id=int, email=dict),
        'trash_email': Topic(email=dict, from_lbl_id=str),
        'email_trashed': Topic(email=dict, from_lbl_id=str, to_remove=list),
        'restore_email': Topic(email=dict),
        'email_restored': Topic(email=dict, to_add=list),
        'delete_email': Topic(label_id=str, message_id=int),
        'email_deleted': Topic(label_id=str),
        'short_sync': Topic(),
        'synced': Topic(history_records=dict),
        ###
        'total_messages': Topic(label_id=str, num_messages=int),
        'modify_labels': Topic(message_id=int, all_labels=str, to_add=tuple, to_remove=tuple),
        'labels_modified': Topic(),
        ###
        'labels_request': Topic(),
        'labels_sync': Topic(labels=dict),
        'label_modified': Topic(label=object),  # Internal
        'label_deleted': Topic(label_id=str),
        'show_label': Topic(label_id=str)  # Internal
    }


class ContactEventChannel(EventChannel):
    topic_map = {
        'page_request': Topic(),
        'page_response': Topic(contacts=list, total_contacts=int),
        'pick_contact': Topic(),  # Internal
        'contact_picked': Topic(email=str),  # Internal
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
        'personal_shortcut': Topic(shortcut=str),
        'social_shortcut': Topic(shortcut=str),
        'updates_shortcut': Topic(shortcut=str),
        'promotions_shortcut': Topic(shortcut=str),
        'forums_shortcut': Topic(shortcut=str),
        'sent_shortcut': Topic(shortcut=str),
        'unread_shortcut': Topic(shortcut=str),
        'important_shortcut': Topic(shortcut=str),
        'starred_shortcut': Topic(shortcut=str),
        'trash_shortcut': Topic(shortcut=str),
        'spam_shortcut': Topic(shortcut=str),
        'send_email_shortcut': Topic(shortcut=str),
        'contacts_shortcut': Topic(shortcut=str),
        'settings_shortcut': Topic(shortcut=str),
    }


class ShortcutEventChannel(EventChannel):
    topic_map = {
        'personal': Topic(),
        'social': Topic(),
        'updates': Topic(),
        'promotions': Topic(),
        'forums': Topic(),
        'sent': Topic(),
        'unread': Topic(),
        'important': Topic(),
        'starred': Topic(),
        'trash': Topic(),
        'spam': Topic(),
        'send_email': Topic(),
        'contacts': Topic(),
        'settings': Topic(),
    }


class ProcessEventChannel(EventChannel):
    topic_map = {
        'commands': Topic(flag=int),
    }
