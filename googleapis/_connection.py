from googleapiclient import discovery
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from oauthlib.oauth2.rfc6749.errors import InvalidClientError

import json


class Singleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, *kwargs)
        return cls._instance


class ConnectionBase(metaclass=Singleton):
    """
    Reasons this class is made into a Singleton:
        1.) There is no need for multiple creations of classes that inherit from ConnectionBase,
            as that will add significant overhead, call "acquire" method instead.
        2.) Instantiating classes that inherit from ConnectionBase on import would be a bad thing,
            because in case of UI creation, that will just add overhead.
        3.) We could use globals and import our class inside some other class or method,
            but that looks terrible and it's violating DRY principle as we have multiple classes that
            inherit from ConnectionBase.
    """
    api_name = ''
    api_version = ''
    client_secret = ''
    storage = ''
    all_scopes = {}
    scopes = ''
    server_port = None

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
        if self.server_port is None:
            raise ValueError("server_port not specified. Usual values are: 8080, 8000, 8888")
        num_fails = 0
        success = False
        while not success:
            try:
                self.credentials = InstalledAppFlow.run_local_server(flow, port=self.server_port)
                success = True
                print(f"Failed to start a local server {num_fails} times.")
            except OSError as err:
                self.server_port += 1
                num_fails += 1
                if num_fails > 100:
                    print("Failed to start a local server more than 100 times.")
                    raise err

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
