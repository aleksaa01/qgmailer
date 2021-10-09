# Label ids are for internal use only.
# This is mainly for efficiency, in order to avoid string allocations and comparisons.
LABEL_ID_PERSONAL = 1
LABEL_ID_UPDATES = 2
LABEL_ID_SOCIAL = 3
LABEL_ID_PROMOTIONS = 4
LABEL_ID_SENT = 5
LABEL_ID_TRASH = 6
###############
# These are ids of labels in Gmail-API. Internally called gmail-labels.
GMAIL_LABEL_PERSONAL = 'CATEGORY_PERSONAL'
GMAIL_LABEL_UPDATES = 'CATEGORY_UPDATES'
GMAIL_LABEL_SOCIAL = 'CATEGORY_SOCIAL'
GMAIL_LABEL_PROMOTIONS = 'CATEGORY_PROMOTIONS'
GMAIL_LABEL_FORUMS = 'CATEGORY_FORUMS'
GMAIL_LABEL_SENT = 'SENT'
GMAIL_LABEL_TRASH = 'TRASH'
GMAIL_LABEL_UNREAD = 'UNREAD'
GMAIL_LABEL_STARRED = 'STARRED'
GMAIL_LABEL_SPAM = 'SPAM'
GMAIL_LABEL_IMPORTANT = 'IMPORTANT'
###############

LABEL_ID_TO_LABEL = {
    LABEL_ID_PERSONAL: GMAIL_LABEL_PERSONAL,
    LABEL_ID_UPDATES: GMAIL_LABEL_UPDATES,
    LABEL_ID_SOCIAL: GMAIL_LABEL_SOCIAL,
    LABEL_ID_PROMOTIONS: GMAIL_LABEL_PROMOTIONS,
    LABEL_ID_SENT: GMAIL_LABEL_SENT,
    LABEL_ID_TRASH: GMAIL_LABEL_TRASH,
}

LABEL_TO_LABEL_ID = {
    GMAIL_LABEL_PERSONAL: LABEL_ID_PERSONAL,
    GMAIL_LABEL_UPDATES: LABEL_ID_UPDATES,
    GMAIL_LABEL_SOCIAL: LABEL_ID_SOCIAL,
    GMAIL_LABEL_PROMOTIONS: LABEL_ID_PROMOTIONS,
    GMAIL_LABEL_SENT: LABEL_ID_SENT,
    GMAIL_LABEL_TRASH: LABEL_ID_TRASH,
    # Gmail api also defines forums label id, which I might add in future.
}

SYSTEM_LABEL = 'system'
USER_LABEL = 'user'


class Label:
    def __init__(self, id, name, type, in_message_list=None, in_label_list=None, total_messages=None,
                 text_color=None, background_color=None):
        self.id = id
        self.name = name
        self.type = type
        self.in_message_list = in_message_list
        self.in_label_list = in_label_list
        self.total_messages = total_messages
        self.text_color = text_color
        self.background_color = background_color
