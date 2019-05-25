from queue import Queue


class ResourceAlreadyReleased(Exception):
    pass


class ResourcePool(object):

    def __init__(self, resource_creator):
        self._creator = resource_creator
        self._qresource = Queue()

    def create(self, num=1):
        for _ in range(num):
            self._qresource.put(self._creator.acquire())

    def get(self):
        return self._qresource.get()

    def put(self, resource):
        self._qresource.put(resource)
        print('ResourcePool size:', self._qresource.qsize())

    def is_empty(self):
        return self._qresource.empty()
