from channels.event_channels import EmailEventChannel, ShortcutEventChannel, ContactEventChannel
from channels.signal_channels import SignalChannel
from googleapis.gmail.labels import *
from views.sidebar import Sidebar
from views.labels.label_view import LabelView
from views.send_email_page import SendEmailPageView
from views.contacts_page import ContactsPageView
from views.options_page import OptionsPageView
from views.email_viewer_page import EmailViewerPageView

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QStackedWidget


# TODO: Add shortcuts here. Category labels should be assigned to top row(Q,W,E...), other labels
#  to middle row(A,S,D...), and other stuff to bottom row(Z,X,C...)
class PageManagerView(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.switch = QStackedWidget(self)
        label_view_page = self.add_page(LabelView())
        send_email_page = self.add_page(SendEmailPageView())
        contacts_page = self.add_page(ContactsPageView())
        settings_page = self.add_page(OptionsPageView())
        email_viewer_page = self.add_page(EmailViewerPageView())

        self.sidebar = Sidebar(self)

        personal_wid = self.sidebar.add_item('Personal', ':images/personal_image.png')
        social_wid = self.sidebar.add_item('Social', ':images/social_image.png')
        updates_wid = self.sidebar.add_item('Updates', ':images/updates_image.png')
        promotions_wid = self.sidebar.add_item('Promotions', ':images/promotions_image.png')
        forums_wid = self.sidebar.add_item('Forums', ':images/forums_image.png')
        categories_label_ids = [
            GMAIL_LABEL_PERSONAL, GMAIL_LABEL_SOCIAL, GMAIL_LABEL_UPDATES,
            GMAIL_LABEL_PROMOTIONS, GMAIL_LABEL_FORUMS
        ]

        group_id = self.sidebar.add_group('Other Labels')
        sent_wid = self.sidebar.add_item_to_group(group_id, 'Sent', ':images/sent_image.png')
        unread_wid = self.sidebar.add_item_to_group(group_id, 'Unread', ':images/unread_image.png')
        important_wid = self.sidebar.add_item_to_group(group_id, 'Important', ':images/important_image.png')
        starred_wid = self.sidebar.add_item_to_group(group_id, 'Starred', ':images/starred_image.png')
        trash_wid = self.sidebar.add_item_to_group(group_id, 'Trash', ':images/trash_image.png')
        spam_wid = self.sidebar.add_item_to_group(group_id, 'Spam', ':images/spam_image.png')
        other_labels_label_ids = [
            GMAIL_LABEL_SENT, GMAIL_LABEL_UNREAD, GMAIL_LABEL_IMPORTANT,
            GMAIL_LABEL_STARRED, GMAIL_LABEL_TRASH, GMAIL_LABEL_SPAM
        ]
        self.item_id_to_label_id = {}
        self.label_id_to_item_id = {}

        send_email_wid = self.sidebar.add_item('Send Email', ':images/send_email_image.png')
        contacts_wid = self.sidebar.add_item('Contacts', ':images/contacts_image.png')
        self.sidebar.add_stretch()
        settings_wid = self.sidebar.add_item('Settings', ':images/options_button.png')

        def item_pressed_handler(widget_id, switch, item_id_to_label_id):
            if widget_id > settings_wid:
                # User defined label
                switch.setCurrentIndex(label_view_page)
                EmailEventChannel.publish(
                    'show_label', label_id=item_id_to_label_id[widget_id])
            elif personal_wid <= widget_id <= forums_wid:
                switch.setCurrentIndex(label_view_page)
                EmailEventChannel.publish('show_label', label_id=categories_label_ids[widget_id])
            elif sent_wid <= widget_id <= spam_wid:
                switch.setCurrentIndex(label_view_page)
                EmailEventChannel.publish(
                    'show_label', label_id=other_labels_label_ids[widget_id - group_id - 1])
            elif widget_id == send_email_wid:
                switch.setCurrentIndex(send_email_page)
            elif widget_id == contacts_wid:
                switch.setCurrentIndex(contacts_page)
            elif widget_id == settings_wid:
                switch.setCurrentIndex(settings_page)

        self.item_pressed_handler = item_pressed_handler
        self.sidebar.on_item_pressed.connect(self.handle_item_pressed)

        def index_changed_handler(page_index, sidebar):
            if page_index == send_email_page:
                sidebar.select_item(send_email_wid)
            elif page_index == contacts_page:
                sidebar.select_item(contacts_wid)
            elif page_index == settings_page:
                sidebar.select_item(settings_wid)
            elif page_index == email_viewer_page:
                sidebar.select_item(None)
            else:
                assert False

        self.index_changed_handler = index_changed_handler

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.switch)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        EmailEventChannel.subscribe(
            'email_response', lambda **kwargs: self.change_to_index(email_viewer_page))

        ContactEventChannel.subscribe(
            'contact_picked', lambda **kwargs: self.change_to_index(send_email_page))
        ContactEventChannel.subscribe(
            'pick_contact', lambda **kwargs: self.change_to_index(contacts_page))

        ShortcutEventChannel.subscribe('personal', lambda **kwargs: self.show_label(personal_wid))
        ShortcutEventChannel.subscribe('social', lambda **kwargs: self.show_label(social_wid))
        ShortcutEventChannel.subscribe('updates', lambda **kwargs: self.show_label(updates_wid))
        ShortcutEventChannel.subscribe('promotions', lambda **kwargs: self.show_label(promotions_wid))
        ShortcutEventChannel.subscribe('forums', lambda **kwargs: self.show_label(forums_wid))
        ShortcutEventChannel.subscribe('sent', lambda **kwargs: self.show_label(sent_wid))
        ShortcutEventChannel.subscribe('unread', lambda **kwargs: self.show_label(unread_wid))
        ShortcutEventChannel.subscribe('important', lambda **kwargs: self.show_label(important_wid))
        ShortcutEventChannel.subscribe('starred', lambda **kwargs: self.show_label(starred_wid))
        ShortcutEventChannel.subscribe('trash', lambda **kwargs: self.show_label(trash_wid))
        ShortcutEventChannel.subscribe( 'spam', lambda **kwargs: self.show_label(spam_wid))
        ShortcutEventChannel.subscribe('send_email', lambda **kwargs: self.show_label(send_email_wid))
        ShortcutEventChannel.subscribe('contacts', lambda **kwargs: self.show_label(contacts_wid))
        ShortcutEventChannel.subscribe('settings', lambda **kwargs: self.show_label(settings_wid))

        self.other_labels_group_id = group_id
        EmailEventChannel.subscribe('labels_sync', self.handle_labels_sync)

        EmailEventChannel.publish('labels_request')

    def handle_item_pressed(self, widget_id):
        self.item_pressed_handler(widget_id, self.switch, self.item_id_to_label_id)

    def add_page(self, page):
        self.switch.addWidget(page)
        return self.switch.count() - 1

    def add_page_switch_rule(self, page_idx, event_channel, topic):
        event_channel.subscribe(topic, lambda **kwargs: self.change_to_index(page_idx))

    def change_to_index(self, page_idx):
        self.switch.setCurrentIndex(page_idx)
        self.index_changed_handler(page_idx, self.sidebar)
    
    def show_label(self, widget_id):
        self.item_pressed_handler(widget_id, self.switch, self.item_id_to_label_id)
        self.sidebar.select_item(widget_id)

    def handle_labels_sync(self, labels, error=''):
        assert not error

        if 'all' in labels:
            for l in labels['all']:
                lbl_obj = Label(*l)
                if lbl_obj.type == USER_LABEL:
                    item_id = self.sidebar.add_item_to_group(
                        self.other_labels_group_id, lbl_obj.name, ':images/label_image.png')
                    self.item_id_to_label_id[item_id] = lbl_obj.id
                    self.label_id_to_item_id[lbl_obj.id] = item_id
        else:
            for l in labels['added']:
                lbl_obj = Label(*l)
                if lbl_obj.type == USER_LABEL:
                    item_id = self.sidebar.add_item_to_group(
                        self.other_labels_group_id, lbl_obj.name, ':images/label_image.png')
                    self.item_id_to_label_id[item_id] = lbl_obj.id
                    self.label_id_to_item_id[lbl_obj.id] = item_id
            for l in labels['modified']:
                lbl_obj = Label(*l)
                if lbl_obj.type == USER_LABEL:
                    item_id = self.label_id_to_item_id[lbl_obj.id]
                    self.sidebar.change_item_name(item_id, lbl_obj.name)
            for l in labels['deleted']:
                lbl_obj = Label(*l)
                if lbl_obj.type == USER_LABEL:
                    item_id = self.label_id_to_item_id[lbl_obj.id]
                    self.sidebar.remove_item(item_id, self.other_labels_group_id)
