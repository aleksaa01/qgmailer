from googleapis._connection import ConnectionBase

API_NAME = 'people'
API_VERSION = 'v1'

CLIENT_SECRET = 'client_secret.json'
STORAGE = 'people_storage.json'

ALL_SCOPES = {
    'contacts': 'https://www.googleapis.com/auth/contacts',
    'readonly_contacts': 'https://www.googleapis.com/auth/contacts.readonly',
    'other_contacts': 'https://www.googleapis.com/auth/contacts.other.readonly',
}

SCOPES = [ALL_SCOPES['contacts'], ALL_SCOPES['other_contacts']]

CLIENT_SECRET_ERROR_MESSAGE = '''
If you don't have client_secret.json file you can acquire it from 
Google API Console at https://console.developers.google.com.
And please ensure that you have enabled People API for your project.
For more information visit https://developers.google.com/people/v1/getting-started.
'''


class PeopleConnection(ConnectionBase):
    api_name = API_NAME
    api_version = API_VERSION
    client_secret = CLIENT_SECRET
    storage = STORAGE
    all_scopes = ALL_SCOPES
    scopes = SCOPES
    server_port = 11000

    def client_secret_error(self):
        raise Exception(CLIENT_SECRET_ERROR_MESSAGE)
