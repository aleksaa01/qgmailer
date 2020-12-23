class SyncHelper(object):
    def __init__(self):
        self._event_queue = []
        # unique local ID counter, used internally for synchronization purposes
        # If you have to sync data with the external API, then add 'ulid' field 
        # to every item in self._data
        self.ulid_counter = 0

    def new_ulid(self):
        """Returns a new unique local ID that's used internally for synchronization purposes."""
        ulid = self.ulid_counter
        self.ulid_counter += 1
        return ulid

    def push_event(self, event_channel, topic, message, item):
        if len(self._event_queue) == 0:
            event_channel.publish(topic, message)
        self._event_queue.append((event_channel, topic, message, item))
    
    def pull_event(self):
        return self._event_queue.pop(0)
    
    def push_next_event(self):
        if len(self._event_queue) > 0:
            event_channel, topic, message, item = self._event_queue[0]
            event_channel.publish(topic, message)
            return event_channel, message, topic, item

    def peek_event(self):
        if len(self._event_queue):
            return self._event_queue[0]

    def events(self):
        return self._event_queue
