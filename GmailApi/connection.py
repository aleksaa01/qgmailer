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


class Connection(object):

    def __init__(self):
        self._conn_list = {}
        self.available_conns = 0

        self.store = file.Storage(STORAGE)
        self.credentials = self.store.get()

        if not self.credentials or self.credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET, SCOPES)
            self.credentials = tools.run_flow(flow, self.store)

    def acquire_connection(self):
        if self.available_conns > 0:
            connection = None
            for con in self._conn_list.values():
                if con.busy is False:
                    connection = con
            if connection is not None:
                self.available_conns -= 1
                return connection

        print('Creating new connection...')
        new_connection = self._establish_new_connection()
        new_connection.busy = True
        self._conn_list[id(new_connection)] = new_connection
        return new_connection

    def release_connection(self, connection):
        conn_id = id(connection)
        self._conn_list[conn_id].busy = False
        self.available_conns += 1

    def _establish_new_connection(self):
        http = self.credentials.authorize(Http())
        connection = discovery.build(API_NAME, API_VERSION, http=http)
        return connection



if __name__ == '__main__':
    def test():
        gmail_connection = Connection()

        service_point1 = gmail_connection.acquire_connection()
        service_point2 = gmail_connection.acquire_connection()
        service_point3 = gmail_connection.acquire_connection()

        a = service_point1.users().getProfile(userId='me').execute()
        b = service_point2.users().getProfile(userId='me').execute()
        c = service_point3.users().getProfile(userId='me').execute()

        gmail_connection.release_connection(service_point1)
        gmail_connection.release_connection(service_point2)
        gmail_connection.release_connection(service_point3)

        service_point1 = gmail_connection.acquire_connection()
        service_point2 = gmail_connection.acquire_connection()
        service_point3 = gmail_connection.acquire_connection()

        print(a['emailAddress'], b['emailAddress'], c['emailAddress'])

    test()
