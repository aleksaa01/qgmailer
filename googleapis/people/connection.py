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

CLIENT_SECRET_ERROR_MESSAGE = '''
If you don't have client_secret.json file you can acquire it from 
Google API Console at https://console.developers.google.com.
And please ensure that you have enabled People API for your project.
For more information visit https://developers.google.com/people/v1/getting-started.
'''


class PConnection(BaseConnection):
    api_name = API_NAME
    api_version = API_VERSION
    client_secret = CLIENT_SECRET
    storage = STORAGE
    all_scopes = ALL_SCOPES
    scopes = SCOPES

    def client_secret_error(self):
        raise Exception(CLIENT_SECRET_ERROR_MESSAGE)
