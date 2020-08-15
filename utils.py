class Singleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class APIEvent(object):
    def __init__(self, event_id, type, category='', value=0):
        self.event_id = event_id
        self.type = type
        self.category = category
        self.value = value
