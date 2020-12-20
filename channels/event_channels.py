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
        'remove_contact': [],   # When user removes a contact
        'contact_removed': [],  # When we get the response from the api
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
