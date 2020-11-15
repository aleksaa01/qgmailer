from PyQt5.QtWidgets import QFrame, QVBoxLayout, QStackedWidget

from channels.event_channels import EmailEventChannel
from channels.signal_channels import SignalChannel


class PageManagerController(object):
    on_event = SignalChannel(int)

    def __init__(self):
        pass

    def add_rule(self, to_page_idx, event_channel, topic):
        event_channel.subscribe(topic, lambda _: self.handle_event(to_page_idx))

    def handle_event(self, to_page_idx):
        self.on_event.emit(to_page_idx)


class PageManagerView(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.c = PageManagerController()
        self.c.on_event.connect(self.change_to_index)

        self.main_layout = QVBoxLayout()
        self.switch = QStackedWidget(self)
        self.main_layout.addWidget(self.switch)
        self.setLayout(self.main_layout)

        # TODO: Delete this, it's just for testing.
        self.setFrameShadow(QFrame.Sunken)
        self.setFrameShape(QFrame.Box)

    def add_page(self, page):
        self.switch.addWidget(page)
        print("Hey widget is added yupi yupi yey!....", type(page))

    def add_rule(self, to_page, event_channel, event_topic):
        """
        Add a rule that specifies to which page you have to switch when someone
        publishes a message on specific event channel and specific topic.
        """
        page_idx = self.switch.indexOf(to_page)
        self.c.add_rule(page_idx, event_channel, event_topic)

    def change_to_page(self, page):
        page_idx = self.switch.indexOf(page)
        self.change_to_index(page_idx)

    def change_to_index(self, page_idx):
        self.switch.setCurrentIndex(page_idx)
        print("Switched to index:", page_idx)
