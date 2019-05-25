from googleapis.gmail.resources import ResourceAlreadyReleased


class ReleasableRequest(object):

    def __init__(self, http_request, release_callback):
        self._http = http_request
        self._callback = release_callback
        self.is_released = False

    def release(self):
        self._callback(self._http)
        self.is_released = True
        del self._http

    def raise_if_released(self):
        if self.is_released:
            raise ResourceAlreadyReleased("Can't execute, resource has been released.")


class MessageRequest(ReleasableRequest):

    def __init__(self, http_request, release_callback, kwargs=None):
        super().__init__(http_request, release_callback)

        self.kwargs = kwargs if kwargs else {}

    def set_arguments(self, **kwargs):
        self.kwargs = kwargs

    def set_id(self, message_id):
        self.kwargs['id'] = message_id

    def execute(self):
        self.raise_if_released()
        return self._http.get(**self.kwargs).execute()


class MessageListRequest(ReleasableRequest):

    def __init__(self, http_request, release_callback, kwargs=None):
        super().__init__(http_request, release_callback)

        self.kwargs = kwargs if kwargs else {}

    def set_arguments(self, **kwargs):
        self.kwargs = kwargs

    def set_page_token(self, token):
        self.kwargs['pageToken'] = token

    def execute(self):
        self.raise_if_released()
        return self._http.list(**self.kwargs).execute()
