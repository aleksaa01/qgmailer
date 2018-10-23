from html import unescape as html_unescape

from GmailApi.gparser import extract_body


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

    def raw(self, resource):
        return extract_body(
            resource.users().messages().get(id=self.id, userId='me', format='raw').execute()
        )
