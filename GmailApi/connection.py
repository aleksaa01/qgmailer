from apiclient import discovery
from httplib2 import Http
from oauth2client import tools, file, client


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



def gmail_establish_connection():
    store = file.Storage(STORAGE)
    credentials = store.get()
    if not credentials:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET, SCOPES)
        credentials = tools.run_flow(flow, store)
    elif credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET, SCOPES)
        credentials = tools.run_flow(flow, store)

    http = credentials.authorize(Http())
    service_point = discovery.build(API_NAME, API_VERSION, http=http)
    return service_point


class ConnectionPool(object):
    pass
