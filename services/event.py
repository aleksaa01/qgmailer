IPC_SHUTDOWN = 1


class APIEvent(object):
    def __init__(self, event_id, category='', value=None):
        self.event_id = event_id
        self.category = category
        self.value = value
