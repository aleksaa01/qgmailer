from googleapis.gmail.resources import ResourceAlreadyReleased
from googleapiclient.discovery import Resource


class ReleasableRequest(object):

    def __init__(self, resource, release_callback, **kwargs):
        self._resource = resource
        self._release_callback = release_callback
        self.is_released = False
        self.kwargs = kwargs if kwargs else {}

    def set_kwargs(self, kwargs):
        self.kwargs = kwargs

    def update_kwargs(self, name, value):
        self.kwargs[name] = value

    def release(self):
        print('Releasing resource', self._release_callback)
        self._release_callback(self._resource)
        self.is_released = True

    def raise_if_released(self):
        if self.is_released:
            raise ResourceAlreadyReleased("Can't execute, resource has been released.")

    def build_request(self):
        raise NotImplementedError()

    def execute(self):
        raise NotImplementedError()

    @property
    def resource(self):
        return self._resource

    @resource.setter
    def resource(self, resource):
        if not isinstance(resource, Resource):
            raise TypeError('Wrong type, resource has to be of type googleapiclient.discovery.Resource')
        self._resource = resource


class MessageRequest(ReleasableRequest):

    def __init__(self, resource, release_callback, **kwargs):
        super().__init__(resource, release_callback, **kwargs)

    def set_id(self, message_id):
        self.kwargs['id'] = message_id

    def build_request(self):
        return self._resource.users().messages().get(**self.kwargs)

    def execute(self):
        self.raise_if_released()
        return self.build_request().execute()


class MessageListRequest(ReleasableRequest):

    def __init__(self, resource, release_callback, **kwargs):
        super().__init__(resource, release_callback, **kwargs)

    def set_page_token(self, token):
        self.kwargs['pageToken'] = token

    def build_request(self):
        return self._resource.users().messages().list(**self.kwargs)

    def execute(self):
        self.raise_if_released()
        return self.build_request().execute()


class BatchRequest(object):

    def __init__(self, resource, response_callback):
        self._batch_request = resource.new_batch_http_request(response_callback)

    def add(self, request):
        self._batch_request.add(request)

    def execute(self):
        return self._batch_request.execute()
