
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
                    f"Keyword argument '{kward_name}' has the wrong type. Expected {val_type}, but got {type(value)} instead.")
        return True


class EventChannel(object):
    topic_map = {}

    @classmethod
    def subscribe(self, topic, callback):
        sub_list = self.topic_map.get(topic)
        if sub_list is None:
            raise ValueError(f'Topic "{topic}" doesn\'t exist.')
        sub_list.append(callback)

    @classmethod
    def publish(self, topic, message):
        sub_list = self.topic_map.get(topic)
        if sub_list is None:
            raise ValueError(f'Topic "{topic}" doesn\'t exist.')

        for sub in sub_list:
            sub(message)


class EmailEventChannel(EventChannel):
    topic_map = {
        'email_request': [],
        'email_response': [],
        'page_request': [],
        'page_response': [],
        'send_email': [],
        'email_sent': [],
    }


class ContactEventChannel(EventChannel):
    topic_map = {
        'page_request': [],
        'page_response': [],
        'pick_contact': [],
        'contact_picked': [],
        'remove_contact': [],
        'contact_removed': [],
        'add_contact': [],
        'contact_added': [],
    }


class OptionEventChannel(EventChannel):
    topic_map = {
        'emails_per_page': [],
        'contacts_per_page': [],
        'font_size': [],
        'theme': [],
    }


class SidebarEventChannel(EventChannel):
    topic_map = {
        'inbox_page': [],
        'email_viewer_page': [],
        'send_email_page': [],
        'contacts_page': [],
        'trash_page': [],
        'options_page': [],
    }
