from services.utils import hex_to_int


class HistoryRecord:
    """
    HistoryRecord represents fused history of changes, of a single email message.
    """
    # Every new record type should have 1 unique bit position set.
    MESSAGE_ADDED = 0x1
    MESSAGE_DELETED = 0x2
    LABELS_ADDED = 0x4
    LABELS_REMOVED = 0x8

    def __init__(self, history_id=None, labels_added=None, labels_removed=None, message=None):
        self.record_types = 0x0
        self.history_id = history_id
        # All label Ids that were added.
        self.labels_added = labels_added or []
        # All label Ids that were removed.
        self.labels_removed = labels_removed or []
        # If message was added, its info can be stored here.
        self.message = message

    def reset(self, history_id):
        # Useful when message has to be deleted.
        self.history_id = history_id
        self.labels_added = []
        self.labels_removed = []
        self.message = None

    def add_type(self, record_type):
        self.record_types |= record_type

    def has_type(self, record_type):
        return self.record_types & record_type

    def labels_modified(self):
        # Use this method to check if you have to update the message.
        # has_type should be used for checking if labels were modified at all.
        return len(self.labels_added) > 0 or len(self.labels_removed) > 0

    def overwrite_types(self, record_type):
        self.record_types = record_type

    def add_labels(self, labels):
        self._fuse_labels(self.labels_added, self.labels_removed, labels)

    def remove_labels(self, labels):
        self._fuse_labels(self.labels_removed, self.labels_added, labels)

    def _fuse_labels(self, put_in, take_from, labels):
        for lbl in labels:
            if lbl in take_from:
                take_from.remove(lbl)
            if lbl not in put_in:
                put_in.append(lbl)


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
        _parse_changes(lbls_added, HistoryRecord.LABELS_ADDED, hid, history_records_map)
    if lbls_removed:
        _parse_changes(lbls_removed, HistoryRecord.LABELS_REMOVED, hid, history_records_map)
    if msgs_added:
        _parse_changes(msgs_added, HistoryRecord.MESSAGE_ADDED, hid, history_records_map)
    if msgs_removed:
        _parse_changes(msgs_removed, HistoryRecord.MESSAGE_DELETED, hid, history_records_map)


def _parse_changes(changed_messages, record_type, history_id, history_records_map):
    for msg in changed_messages:
        msg_id = hex_to_int(msg['message']['id'])
        history_record = history_records_map.get(msg_id)

        if record_type == HistoryRecord.MESSAGE_DELETED:
            if history_record is None:
                history_record = HistoryRecord(history_id)
                history_record.add_type(HistoryRecord.MESSAGE_DELETED)
            else:
                history_record.reset(history_id)
                # Overwrite any applied record types.
                history_record.overwrite_types(HistoryRecord.MESSAGE_DELETED)
        elif record_type == HistoryRecord.MESSAGE_ADDED:
            # Because new message was added, we know that history_record must be None prior to this.
            history_record = HistoryRecord(history_id)
            history_record.add_type(HistoryRecord.MESSAGE_ADDED)
        elif record_type == HistoryRecord.LABELS_ADDED:
            changed_labels = msg.get('labelIds')
            if history_record is None:
                history_record = HistoryRecord(history_id)
            history_record.add_type(HistoryRecord.LABELS_ADDED)
            history_record.add_labels(changed_labels)
        elif record_type == HistoryRecord.LABELS_REMOVED:
            changed_labels = msg.get('labelIds')
            if history_record is None:
                history_record = HistoryRecord(history_id)
            history_record.add_type(HistoryRecord.LABELS_REMOVED)
            history_record.remove_labels(changed_labels)
        else:
            raise TypeError(f"Invalid record type: {record_type}")

        history_records_map[msg_id] = history_record
