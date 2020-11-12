from views.views import EventChannel


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
        'send_email_response': [],
    }


class OptionEventChannel(EventChannel):
    topic_map = {
        'email_page_length': [],
    }
