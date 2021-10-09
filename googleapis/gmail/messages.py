from html import unescape as html_unescape
import asyncio


class EmailMessage(object):
    def __init__(self, message_id=None, thread_id=None, history_id=None, field_to=None,
                 field_from=None, subject=None, snippet=None, internal_date=None, label_ids=None):
        self.message_id = message_id
        self.thread_id = thread_id
        self.history_id = history_id
        self.field_to = field_to
        self.field_from = field_from
        self.subject = subject
        self.snippet = snippet
        self.internal_date = internal_date
        self.label_ids = label_ids


def parse_all_email_messages(messages):
    # Parse email messages in place
    for idx, msg in enumerate(messages):
        email_message = parse_email_message(msg)
        messages[idx] = email_message


async def async_parse_all_email_messages(messages, await_after=10):
    # Parse email messages in place
    for idx, msg in enumerate(messages):
        email_message = parse_email_message(msg)
        messages[idx] = email_message
        # Await on every 10 processed messages.
        if idx % await_after == 0:
            await asyncio.sleep(0)


def parse_email_message(message):
    email_message = EmailMessage()
    email_message.message_id = int(message.get('id'), 16)
    email_message.thread_id = int(message.get('threadId'), 16)
    email_message.history_id = int(message.get('historyId'))
    email_message.snippet = html_unescape(message.get('snippet'))
    # Serialize label ids, every label id is prefixed by comma(",")
    email_message.label_ids = ','.join(message.get('labelIds'))
    email_message.internal_date = int(message.get('internalDate'))
    # internal_timestamp = date_to_timestamp(message.get('internalDate'))
    # email_message.date = datetime.datetime.fromtimestamp(internal_timestamp).strftime('%b %d')
    for field in message.get('payload').get('headers'):
        field_name = field.get('name').lower()
        if field_name == 'from':
            email_message.field_from = field.get('value').split('<')[0]
        elif field_name == 'to':
            email_message.field_to = field.get('value').split('<')[0].split('@')[0]
        elif field_name == 'subject':
            email_message.subject = field.get('value') or '(no subject)'
    email_message.field_from = email_message.field_from or ''
    email_message.field_to = email_message.field_to or ''
    return email_message
