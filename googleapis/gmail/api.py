from googleapis.gmail.resources import ResourcePool
from googleapis.gmail.requests import MessageRequest, MessageListRequest


class GmailApi(object):

    """
    GmailApi provides methods for interaction with Google's Gmail-API.
    Every method that interacts with the API should return http request and not actual results.
    That way you can pass those http requests to separate threads and execute them there.
    """

    def __init__(self, gmail_resource):
        self.resource_pool = ResourcePool(gmail_resource)

    def list_messages(self, **kwargs):
        self._create_if_empty()

        resource = self.resource_pool.get()
        http_request = resource.users().messages()

        return MessageListRequest(http_request, self.release_resource, kwargs)

    def get_message(self, **kwargs):
        self._create_if_empty()

        resource = self.resource_pool.get()
        http_request = resource.users().messages()

        return MessageRequest(http_request, self.release_resource, kwargs)

    def _create_if_empty(self):
        if self.resource_pool.is_empty():
            self.resource_pool.create()

    def release_resource(self, resource):
        self.resource_pool.put(resource)
