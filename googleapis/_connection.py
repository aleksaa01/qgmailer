from googleapiclient import discovery
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from oauthlib.oauth2.rfc6749.errors import InvalidClientError

import json


class ConnectionBase(object):
    api_name = ''
    api_version = ''
    client_secret = ''
    storage = ''
    all_scopes = {}
    scopes = ''

    def __init__(self):
        self._res_list = []
        self.user_config = None
        self.credentials = None
        try:
            self.authorize_user()
            # if user is successfully authorized, no need to call run_flow so just return
            return
        except (ValueError, FileNotFoundError):
            # user config file doesn't exist or is invalid, ignore error and call run_flow
            pass
        try:
            self.run_flow()
        except (FileNotFoundError, InvalidClientError):
            self.client_secret_error()

    def authorize_user(self):
        if self.user_config is None:
            with open(self.storage, 'r') as file:
                self.user_config = json.load(file)

        self.credentials = Credentials.from_authorized_user_info(self.user_config, self.scopes)

    def run_flow(self):
        with open(self.client_secret, 'r') as file:
            client_config = json.load(file)

        flow = InstalledAppFlow.from_client_config(client_config, self.scopes)
        self.credentials = InstalledAppFlow.run_local_server(flow)

        # save obtained credentials for faster authorization next time
        self.save_credentials()

    def save_credentials(self):
        user_config = {}
        with open(self.storage, 'w') as file:
            user_config['refresh_token'] = self.credentials.refresh_token
            user_config['client_id'] = self.credentials.client_id
            user_config['client_secret'] = self.credentials.client_secret
            self.user_config = user_config
            json.dump(user_config, file)

    def client_secret_error(self):
        raise NotImplementedError('Classes that inherit from {} have to implement this method.'.format(type(self).__name__))

    def acquire(self):
        # Acquire new connection
        new_resource = self._establish_new_connection()
        self._res_list.append(new_resource)
        return new_resource

    def _establish_new_connection(self):
        """ Returns a Resource object for interacting with an API."""
        resource = discovery.build(self.api_name, self.api_version, credentials=self.credentials)
        return resource
