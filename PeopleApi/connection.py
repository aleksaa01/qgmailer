from httplib2 import Http
from oauth2client import tools, file, client
from googleapiclient import discovery


API_NAME = 'people'
API_VERSION = 'v1'

CLIENT_SECRET = 'client_secret.json'
STORAGE = 'people_storage.json'

ALL_SCOPES = {
    'write': 'https://www.googleapis.com/auth/contacts',
    'read': 'https://www.googleapis.com/auth/contacts.readonly'
}

SCOPES = ALL_SCOPES['write']


class PConnection(object):

    def __init__(self):
        self._res_list = []

        self.store = file.Storage(STORAGE)
        self.credentials = self.store.get()

        if not self.credentials or self.credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET, SCOPES)
            self.credentials = tools.run_flow(flow, self.store)

    def acquire(self):
        # Acquire new connection
        print('Creating new people connection...')
        new_resource = self._establish_new_connection()
        self._res_list.append(new_resource)
        return new_resource

    def _establish_new_connection(self):
        """ Returns a Resource object for interacting with an API."""
        http = self.credentials.authorize(Http())
        resource = discovery.build(API_NAME, API_VERSION, http=http)
        return resource

