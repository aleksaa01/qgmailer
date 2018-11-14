from httplib2 import Http
from oauth2client import tools, file, client
from googleapiclient import discovery


API_NAME = 'gmail'
API_VERSION = 'v1'

CLIENT_SECRET = 'client_secret.json'
STORAGE = 'gmail_storage.json'

ALL_SCOPES = {
    'read':               'https://www.googleapis.com/auth/gmail.readonly',
    'compose':            'https://www.googleapis.com/auth/gmail.compose',
    'send':               'https://www.googleapis.com/auth/gmail.send',
    'insert':             'https://www.googleapis.com/auth/gmail.insert',
    'modify':             'https://www.googleapis.com/auth/gmail.modify',
    'metadata':           'https://www.googleapis.com/auth/gmail.metadata',
    'basic_settings':     'https://www.googleapis.com/auth/gmail.settings.basic',
    'sensitive_settings': 'https://www.googleapis.com/auth/gmail.settings.sharing',
    'full_access':        'https://mail.google.com/'
}

SCOPES = ALL_SCOPES['modify']


class GConnection(object):

    def __init__(self):
        self._res_list = []

        self.store = file.Storage(STORAGE)
        self.credentials = self.store.get()

        if not self.credentials or self.credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET, SCOPES)
            self.credentials = tools.run_flow(flow, self.store)

    def acquire(self):
        # Acquire new connection
        print('Creating new gmail connection...')
        new_resource = self._establish_new_connection()
        self._res_list.append(new_resource)
        return new_resource

    def _establish_new_connection(self):
        """ Returns a Resource object for interacting with an API."""
        http = self.credentials.authorize(Http())
        resource = discovery.build(API_NAME, API_VERSION, http=http)
        return resource
