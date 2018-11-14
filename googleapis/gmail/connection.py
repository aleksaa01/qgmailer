from googleapis._connection import BaseConnection


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


class GConnection(BaseConnection):
    api_name = API_NAME
    api_version = API_VERSION
    client_secret = CLIENT_SECRET
    storage = STORAGE
    all_scopes = ALL_SCOPES
    scopes = SCOPES
