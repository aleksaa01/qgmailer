from googleapis._connection import BaseConnection

API_NAME = 'people'
API_VERSION = 'v1'

CLIENT_SECRET = 'client_secret.json'
STORAGE = 'people_storage.json'

ALL_SCOPES = {
    'write': 'https://www.googleapis.com/auth/contacts',
    'read': 'https://www.googleapis.com/auth/contacts.readonly'
}

SCOPES = ALL_SCOPES['write']


class PConnection(BaseConnection):
    api_name = API_NAME
    api_version = API_VERSION
    client_secret = CLIENT_SECRET
    storage = STORAGE
    all_scopes = ALL_SCOPES
    scopes = SCOPES
