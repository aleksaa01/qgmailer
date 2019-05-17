from html import unescape as html_unescape
from datetime import datetime

from googleapis.gmail.gparser import extract_body


class ThreadObject(object):

    def __init__(self, thread_dict):
        self.id = thread_dict['id']
        self.snippet = html_unescape(thread_dict['snippet'])
        self.historyId = thread_dict['historyId']


class MessageObject(object):

    def __init__(self, message_dict):
        self.id = message_dict['id']
        self.snippet = html_unescape(message_dict['snippet'])
        self.thread_id = message_dict['threadId']
        self.label_ids = message_dict['labelIds']
        self.history_id = message_dict['historyId']
        # message_dict['internalDate'] - The internal message creation timestamp in milliseconds
        self.internalDate = datetime.fromtimestamp(int(message_dict['internalDate']) / 1000)

    def raw(self, resource):
        return extract_body(
            resource.users().messages().get(id=self.id, userId='me', format='raw').execute()
        )


class MessageBase(object):

    def __init__(self, message_resource):
        try:
            self.extract_data(message_resource)
        except Exception as err:
            print('HUH', message_resource)
            raise Exception()


class MinimalMessage(MessageBase):

    def __init__(self, message_resource):
        super().__init__(message_resource)

    def extract_data(self, message_resource):
        self.id = message_resource['id']
        self.thread_id = message_resource['threadId']
        self.snippet = html_unescape(message_resource['snippet'])
        self.history_id = message_resource['historyId']
        # message_dict['internalDate'] - The internal message creation timestamp in milliseconds
        self.internalDate = datetime.fromtimestamp(int(message_resource['internalDate']) / 1000)

        # Set "from" and "subject" attributes.
        headers = message_resource['payload']['headers'] # dict
        if len(headers) == 2:
            self.from_field = headers[0]['value'].split('<')[0]
            self.subject_field = headers[1]['value']
        elif len(headers) == 1:
            if headers[0]['name'] == 'From':
                self.from_field = headers[0]['value'].split('<')[0]
                self.subject_field = '(no subject)'
            else:
                self.subject_field = headers[0]['value']
                self.from_field = 'Unknown'
        else:
            raise Exception('Headers are empty.')

        # self.message_resource = message_resource
