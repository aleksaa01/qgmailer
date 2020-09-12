class Singleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


IPC_SHUTDOWN = 1

class APIEvent(object):
    def __init__(self, event_id, category='', value=None):
        self.event_id = event_id
        self.category = category
        self.value = value