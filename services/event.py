IPC_SHUTDOWN = 1


class APIEvent(object):
    def __init__(self, event_id, event_channel, topic, **payload):
        self.event_id = event_id
        self.event_channel = event_channel
        self.topic = topic
        self.payload = payload
