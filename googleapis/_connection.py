from httplib2 import Http
from oauth2client import tools, file, client
from googleapiclient import discovery
from oauth2client.clientsecrets import InvalidClientSecretsError

class BaseConnection(object):
    api_name = ''
    api_version = ''
    client_secret = ''
    storage = ''
    all_scopes = {}
    scopes = ''

    def __init__(self):
        self._res_list = []

        self.store = file.Storage(self.storage)
        self.credentials = self.store.get()

        if not self.credentials or self.credentials.invalid:
            try:
                flow = client.flow_from_clientsecrets(self.client_secret, self.scopes)
                self.credentials = tools.run_flow(flow, self.store)
            except InvalidClientSecretsError:
                self.client_secret_error()

    def client_secret_error(self):
        raise NotImplemented('Classes that inherit from BaseConnection have to implement this method.')

    def acquire(self):
        # Acquire new connection
        new_resource = self._establish_new_connection()
        self._res_list.append(new_resource)
        return new_resource

    def _establish_new_connection(self):
        """ Returns a Resource object for interacting with an API."""
        http = self.credentials.authorize(Http())
        resource = discovery.build(self.api_name, self.api_version, http=http)
        return resource
