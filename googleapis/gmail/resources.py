from queue import Queue
from utils import Singleton


class ResourceAlreadyReleased(Exception):
    pass


class ResourcePool(object, metaclass=Singleton):

    def __init__(self, resource_creator):
        self._creator = resource_creator
        self._qresource = Queue()

    def create(self, num=1):
        for _ in range(num):
            self._qresource.put(self._creator.acquire())

    def get(self):
        print('ResourcePool decreased...')
        if self.is_empty():
            self.create()

        return self._qresource.get()

    def put(self, resource):
        self._qresource.put(resource)
        print('ResourcePool increased:', self._qresource.qsize())

    def is_empty(self):
        return self._qresource.empty()
