class EmailMessage(object):
    def __init__(self, pk=None, message_id=None, thread_id=None, history_id=None, field_to=None,
                 field_from=None, subject=None, snippet=None, internal_date=None):
        self.pk = pk
        self.message_id = message_id,
        self.thread_id = thread_id
        self.history_id = history_id
        self.field_to = field_to
        self.field_from = field_from
        self.subject = subject
        self.snippet = snippet
        self.internal_date = internal_date

        self.date = None
        self.label_ids = None

