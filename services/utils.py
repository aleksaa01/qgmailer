from googleapis.gmail.labels import GMAIL_LABEL_UNREAD
from googleapis.gmail.messages import EmailMessage
import datetime


def email_message_to_dict(email_message):
    data = vars(email_message)
    internal_timestamp = internal_date_to_timestamp(email_message.internal_date)
    data['date'] = datetime.datetime.fromtimestamp(internal_timestamp).strftime('%b %d')
    data['unread'] = GMAIL_LABEL_UNREAD in email_message.label_ids
    return data


def db_message_to_dict(row):
    date = datetime.datetime.fromtimestamp(internal_date_to_timestamp(row[7])).strftime("%b %d")
    return {
        'message_id': row[0], 'thread_id': row[1], 'history_id': row[2], 'field_to': row[3],
        'field_from': row[4], 'subject': row[5], 'snippet': row[6], 'internal_date': row[7],
        'label_ids': row[8], 'date': date, 'unread': GMAIL_LABEL_UNREAD in row[8]
    }


def db_message_to_email_message(row):
    return EmailMessage(*row)


def timestamp_to_internal_date(timestamp):
    # Datetime timestamp to internal date(email_message.internal_date)
    return int(timestamp * 1000)


def internal_date_to_timestamp(internal_date):
    # Internal date(email_message.internal_date) to datetime timestamp.
    return int(internal_date) / 1000


def int_to_hex(int_message_id):
    return hex(int_message_id)[2:]


def hex_to_int(hex_message_id):
    return int(hex_message_id, 16)
