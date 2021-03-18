from googleapis.gmail.labels import LABEL_TO_LABEL_ID, LABEL_ID_TRASH, LABEL_ID_SENT, \
    GMAIL_LABEL_TRASH, GMAIL_LABEL_SENT


class HistoryRecord(object):
    LABEL_TYPE_INBOX = 1
    LABEL_TYPE_SENT = 2
    ACTION_TRASH = 3
    ACTION_RESTORE = 4
    ACTION_ADD = 5
    ACTION_DELETE = 6

    def __init__(self, action=None, initial_label_id=None,
                 message_id=None, history_id=None, label_type=None):
        self.action = action
        self.initial_label_id = initial_label_id
        self.message_id = message_id
        self.history_id = history_id
        self.label_type = label_type

        self.email = None

    def set_record_info(self, action=None, initial_label_id=None,
                        message_id=None, history_id=None, label_type=None):
        self.action = action
        self.initial_label_id = initial_label_id
        self.message_id = message_id
        self.history_id = history_id
        self.label_type = label_type

    def set_email(self, email):
        self.email = email


def parse_history_record(history_record, history_records_map):
    """
    :param history_record: Dictionary with keys: labelsAdded, labelsRemoved,
    messagesAdded, messagesRemoved
    :param history_records_map: Dictionary of <ID: HistoryRecord>
    """
    hid = history_record['id']
    lbls_added = history_record.get('labelsAdded', [])
    lbls_removed = history_record.get('labelsRemoved', [])
    msgs_added = history_record.get('messagesAdded', [])
    msgs_removed = history_record.get('messagesDeleted', [])

    if lbls_added:
        _parse_changes(lbls_added, HistoryRecord.ACTION_TRASH, hid, history_records_map)
    if lbls_removed:
        _parse_changes(lbls_removed, HistoryRecord.ACTION_RESTORE, hid, history_records_map)
    if msgs_added:
        _parse_changes(msgs_added, HistoryRecord.ACTION_ADD, hid, history_records_map)
    if msgs_removed:
        _parse_changes(msgs_removed, HistoryRecord.ACTION_DELETE, hid, history_records_map)


def _parse_changes(changed_messages, action_type, history_id, history_records_map):
    for msg in changed_messages:
        message_labels = msg['message']['labelIds']
        # labelIds can be empty, for example for new email.
        changed_labels = msg.get('labelIds')

        if action_type == HistoryRecord.ACTION_TRASH or action_type == HistoryRecord.ACTION_RESTORE:
            # Check if TRASH label was added to this email message and proceed, continue otherwise
            if GMAIL_LABEL_TRASH not in changed_labels:
                continue

        # Figure out what type of email are we dealing with, this will make it easy for others to
        # determine what metadata has to be fetched.
        label_id = None
        label_type = None
        if GMAIL_LABEL_SENT in message_labels:
            label_type = HistoryRecord.LABEL_TYPE_SENT
            label_id = LABEL_ID_SENT
        else:
            for lbl in message_labels:
                # Here we check if we can handle this label(for example DRAFT label is not handled)
                label_id = LABEL_TO_LABEL_ID.get(lbl)
                # Here we are figuring out initial label of this message
                if label_id is not None and label_id != LABEL_ID_TRASH:
                    label_type = HistoryRecord.LABEL_TYPE_INBOX
                    # Break once you find a label_type, otherwise label_id might change the value.
                    break
        # If label_type is None, then there either is no real change, or we don't support that label.
        if label_type is None:
            continue
        # We have to execute previous code to determine correct label_type, but if message was
        # deleted, we care about the EXACT location of that message before it was deleted, which means
        # that we have to check if message was present in the trash and override it if that's the case.
        if action_type == HistoryRecord.ACTION_DELETE and GMAIL_LABEL_TRASH in message_labels:
            label_id = LABEL_ID_TRASH

        msg_id = msg['message']['id']

        history_record = history_records_map.get(msg_id)
        # Add new history record if it's not already present, modify record info otherwise.
        if history_record is None:
            history_record = HistoryRecord(action_type, label_id,
                                           msg_id, history_id, label_type)
            history_records_map[msg_id] = history_record
        else:
            history_record.set_record_info(action_type, label_id,
                                           msg_id, history_id, label_type)
