class EmailMessage(object):
    def __init__(self, message_id=None, thread_id=None, history_id=None, field_to=None,
                 field_from=None, subject=None, snippet=None, internal_date=None, label_ids=None):
        self.message_id = message_id,
        self.thread_id = thread_id
        self.history_id = history_id
        self.field_to = field_to
        self.field_from = field_from
        self.subject = subject
        self.snippet = snippet
        self.internal_date = internal_date
        self.label_ids = label_ids

        self.date = None


def dtime_idate(timestamp):
    # Datetime timestamp to internal date(email_message.internal_date)
    return int(timestamp * 1000)


def idate_dtime(internal_date):
    # Internal date(email_message.internal_date) to datetime timestamp.
    return int(internal_date) / 1000
