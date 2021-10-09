IPC_SHUTDOWN = 1
NOTIFICATION_ID = -1


class APIEvent(object):
    # FIXME: Why payload here acts as a keyword argument catcher ?
    #  Make it a normal argument: payload=None
    def __init__(self, event_id, event_channel, topic, **payload):
        self.event_id = event_id
        self.event_channel = event_channel
        self.topic = topic
        self.payload = payload
