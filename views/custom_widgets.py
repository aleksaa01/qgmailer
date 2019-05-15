from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QSpacerItem, \
    QSizePolicy, QPushButton, QListView, QApplication, QVBoxLayout, QDialog, \
    QLineEdit, QComboBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QIcon, QPixmap

from models.attachments import AttachmentListModel
from googleapis.people.contact_objects import ContactObject

import re


class PagedList(QWidget):
    """
    :param type:  Current types: personal, social, promotions, updates...
           Type is used to recognize and distinguish widgets.
    :param size:  Size of this widget.
    :param parent: Widget's parent.
    """

    def __init__(self, type=None, size=tuple(), parent=None):
        super().__init__(parent)

        if not isinstance(size, tuple):
            raise TypeError('Size must be a tuple: (width, height)')

        self.type = type
        self._model = None

        # default size
        if not parent:
            self.width = 900
            self.height = 550

        if size and isinstance(size, tuple):
            self.width = size[0]
            self.height = size[1]
            self.setMinimumSize(size[0], size[1])

        layout = QVBoxLayout()

        self.container = QWidget()
        self.container.setMinimumSize(0, 0)
        self.pagedIndexBox = PagedIndex(self.container)
        layout.addWidget(self.container)

        self.list_view = QListView()
        self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # adjustSize() - Adjusts the size of the widget to fit its contents.
        # This function uses sizeHint() if it is valid, i.e., the size hint's width and height are >= 0.
        # Otherwise, it sets the size to the children rectangle that covers all child widgets
        # (the union of all child widget rectangles).
        self.list_view.adjustSize()
        self.list_view.setUniformItemSizes(True)  # Enables Qt to do some optimizations.
        layout.addWidget(self.list_view)

        self.setLayout(layout)

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, model):
        self._model = model
        self.list_view.setModel(model)

        self._model.indexesChanged.connect(self.change_indexes)

    def link_items(self, f):
        """
        :param f: Function to be called when ListView item is clicked.
        """
        self.list_view.clicked.connect(f)

    def link_navigation(self):
        # TODO: Delete this, viewmodel should be responsible for this.
        self.pagedIndexBox.next.clicked.connect(self._model.loadNext)
        self.pagedIndexBox.previous.clicked.connect(self._model.loadPrevious)

    def link_indexes(self):
        # TODO: Delete this, do this in setModel instead.
        self._model.indexesChanged.connect(self.change_indexes)

    def change_indexes(self, begin, end):
        self.pagedIndexBox.indexLabel = '{} - {}'.format(begin, end)


class PagedIndex(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.horizontalLayout = QHBoxLayout(parent)
        self.horizontalLayout.setContentsMargins(5, 1, 5, 1)
        self.horizontalLayout.setSpacing(0)

        self._indexLabel = QLabel("0 - 0", parent)
        self.horizontalLayout.addWidget(self._indexLabel)

        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)

        self.previous = QPushButton(parent)
        self.previous.setObjectName('personalPreviousBtn')
        self.previous.setMaximumSize(40, 40)
        self.previous.setCursor(QCursor(Qt.PointingHandCursor))
        self.previous.setText("")
        icon6 = QIcon()
        icon6.addPixmap(QPixmap(":/images/previous_button.png"), QIcon.Normal, QIcon.Off)
        self.previous.setIcon(icon6)
        self.previous.setIconSize(QSize(20, 20))
        self.horizontalLayout.addWidget(self.previous)

        self.next = QPushButton(parent)
        self.next.setObjectName('personalNextBtn')
        self.next.setMaximumSize(40, 40)
        self.next.setCursor(QCursor(Qt.PointingHandCursor))
        self.next.setText("")
        icon7 = QIcon()
        icon7.addPixmap(QPixmap(":/images/next_button.png"), QIcon.Normal, QIcon.Off)
        self.next.setIcon(icon7)
        self.next.setIconSize(QSize(20, 20))
        self.horizontalLayout.addWidget(self.next)

    @property
    def indexLabel(self):
        self._indexLabel.text()

    @indexLabel.setter
    def indexLabel(self, s):
        self._indexLabel.setText(s)


class AttachmentViewer(QWidget):

    fileExtracted = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedWidth(220)

        layout = QVBoxLayout()

        self.label = QLabel('Attachments')
        layout.addWidget(self.label)

        self._list_view = QListView()
        self._list_model = AttachmentListModel()
        self._list_view.setModel(self._list_model)
        layout.addWidget(self._list_view)

        self._list_view.clicked.connect(self.emit_file)

        self.setLayout(layout)

    def emit_file(self, index):
        print('Clicked on attachment')
        self.fileExtracted.emit(
            self._list_model.extractFilename(index),
            self._list_model.extractPayload(index)
        )

    def clear_attachments(self):
        self._list_model.clearData()

    def append_attachments(self, attachments):
        self._list_model.addData(attachments)

        # if there are no attachments just hide the ListView.
        if not self._list_model.checkData():
            self.hide()
        elif self.isHidden():
            self.show()


class ResourceNotAssignedError(Exception):
    pass


class EmailViewer(QWidget):

    fileExtracted = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()

        self._web_engine = QWebEngineView(self)
        self.email_page = self._web_engine.page()
        layout.addWidget(self._web_engine)

        self.attachment_viewer = AttachmentViewer(self)
        self.attachment_viewer.fileExtracted.connect(
            lambda filename, file: self.fileExtracted.emit(filename, file)
        )
        layout.addWidget(self.attachment_viewer)

        self.setLayout(layout)

        self.res = None
        self.stop_extracting = False
        self._current_messages = []

    def update_content(self, message_objects):
        if self.res is None:
            raise ResourceNotAssignedError('You have to assign a resource to EmailViewer first.')

        self.attachment_viewer.clear_attachments()

        self._current_messages.clear()
        self.email_page.runJavaScript('document.open();')
        self.email_page.runJavaScript('document.write("");')

        for msg in message_objects:
            # Give your app a second to process some events
            # and see if user changed the page.
            QApplication.processEvents()

            if self.stop_extracting is True:
                print("STOPPING EXTRACTION...")
                self.stop_extracting = False
                self.email_page.runJavaScript('document.close();')
                break

            self._append_content(msg.raw(self.res))

        self.email_page.runJavaScript('document.close();')
        self._current_messages = message_objects

    def _append_content(self, body_and_attachments):
        self.email_page.runJavaScript('document.write(`{}`);'.format(body_and_attachments[0]))
        self.attachment_viewer.append_attachments(body_and_attachments[1])

    def assign_resource(self, resource):
        # You assign resource using this method instead of passing a resource
        # to the constructor because this widget should be created in View not Dispatcher.
        self.res = resource


class OptionItem(QWidget):

    def __init__(self, option, value, current_value, parent=None):
        super().__init__(parent)

        self.option = option
        self.value = value
        self.current_value = current_value

        self.layout = QHBoxLayout()

        self.option_widget = QLabel(option.replace('_', ' ').capitalize())

        if type(value) == int:
            self.value_widget = QLineEdit(str(current_value))

        elif type(value) == str:
            self.value_widget = QLineEdit(value)

        elif type(value) == list:
            self.value_widget = QComboBox()
            self.value_widget.addItems([str(i) for i in value])
            index = self.value_widget.findText(str(self.current_value))
            self.value_widget.setCurrentIndex(index)

        self.layout.addWidget(self.option_widget)
        self.layout.addWidget(self.value_widget)
        self.setLayout(self.layout)

    def extract_value(self):
        if type(self.value) == str:
            return self.value_widget.text()

        elif type(self.value) == int:
            return int(self.value_widget.text())

        elif type(self.value) == list:
            return self.value_widget.currentText()


class OptionsDialog(QDialog):
    """
    OptionsDialog should interact with Option object.
    """

    def __init__(self, option_obj, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Options')
        icon = QIcon()
        icon.addPixmap(QPixmap(":/images/qgmailer_logo.png"), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)
        self._options = option_obj

        self.layout = QVBoxLayout()
        self.setup()

    def setup(self):
        # Add item that hold all the themes

        all_opts = self._options.all_options.items()
        app_opts = self._options.app_options.items()
        for al, ap in zip(all_opts, app_opts):
            # al[0], a[1], ap[1] - option, value/values, current_value
            self.add_option_widget(al[0], al[1], ap[1])

        container = QWidget()
        container_layout = QHBoxLayout()
        ok_btn = QPushButton('OK')
        cancel_btn = QPushButton('Cancel')
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        container_layout.addWidget(ok_btn)
        container_layout.addWidget(cancel_btn)
        container.setLayout(container_layout)

        self.layout.addWidget(container)
        self.setLayout(self.layout)

    def add_option_widget(self, option, value, current_value):
        # if value is of a type int, make TextEdit
        # if value is of a type list, make ComboBox
        self.layout.addWidget(OptionItem(option, value, current_value))

    # def add_option_widgets(self, options):
    #     for option, value in options.items():
    #         self.add_option_widget(option, value)

    def accept(self):
        index = self.layout.count() - 1
        while index >= 0:
            item = self.layout.itemAt(index).widget()
            if not isinstance(item, OptionItem):
                index -= 1
                continue
            self._options.change_option(item.option, item.extract_value(), save=False)
            index -= 1

        self._options.save()
        super().accept()


class AddContactDialog(QDialog):

    def __init__(self, contacts_model, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Add Contact')
        icon = QIcon()
        icon.addPixmap(QPixmap(":/images/qgmailer_logo.png"), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)
        self._model = contacts_model

        self.name_field = None
        self.email_field = None
        self.EMAIL_REGEX = re.compile(r'[^@]+@[^@]+\.[^@]+')

        self.layout = QVBoxLayout()
        self.setup()

        buttons_layout = QHBoxLayout()

        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.clicked.connect(self.close)
        self.ok_btn = QPushButton('OK')
        self.ok_btn.clicked.connect(self.accept)

        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.ok_btn)
        self.layout.addLayout(buttons_layout)
        self.setLayout(self.layout)

    def setup(self):
        fields_layout = QHBoxLayout()
        layout1 = QVBoxLayout()
        layout2 = QVBoxLayout()

        name_label = QLabel('Name:')
        self.name_field = QLineEdit()
        layout1.addWidget(name_label)
        layout1.addWidget(self.name_field)

        email_label = QLabel('Email:')
        self.email_field = QLineEdit()
        self.email_field.textEdited.connect(lambda e: self.email_field.setStyleSheet(''))
        layout2.addWidget(email_label)
        layout2.addWidget(self.email_field)

        fields_layout.addLayout(layout1)
        fields_layout.addLayout(layout2)
        self.layout.addLayout(fields_layout)


    def accept(self):
        contact = ContactObject()
        contact.name = self.name_field.text()

        email = self.email_field.text()
        if not self.EMAIL_REGEX.match(email):
            self.email_field.setStyleSheet('border: 1px solid red;')
            return
        contact.email = email


        self._model.add_contact(contact)

        super().accept()


class ErrorReportingDialog(QDialog):

    def __init__(self, message, parent=None):
        super().__init__(parent)

        self.setFixedSize(300, 100)

        layout = QVBoxLayout()

        message_label = QLabel(message)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        ok_btn = QPushButton('OK')
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)

        self.setLayout(layout)


class OptionItemComboBox(QWidget):

    def __init__(self, option_name, display_text, possible_options, current_option, parent=None):
        super().__init__(parent)

        self.name = option_name

        if isinstance(current_option, int):
            self._convert = lambda x: int(x)
            self.options = [str(opt) for opt in possible_options]
            current_option = str(current_option)
        else:
            # Else it's string
            self._convert = lambda x: x
            self.options = possible_options

        label = QLabel(display_text, self)
        self.options_combobox = QComboBox(self)
        self.options_combobox.addItems(self.options)
        self.options_combobox.setCurrentIndex(self.options.index(current_option))

        mlayout = QHBoxLayout()
        mlayout.addWidget(label)
        mlayout.addWidget(self.options_combobox)
        self.setLayout(mlayout)

    def validate(self):
        return True

    def get_current_option(self):
        curr_index = self.options_combobox.currentIndex()
        return self._convert(self.options[curr_index])


class OptionItemTextEdit(QWidget):

    def __init__(self, option_name, displayed_text, current_option, validator=None, parent=None):
        super().__init__(parent)

        self.name = option_name

        if isinstance(current_option, int):
            self._convert = lambda x: int(x)
            current_option = str(current_option)
        else:
            self._convert = lambda x: x

        self.validator = validator

        label = QLabel(displayed_text, self)
        self.current_option = current_option
        self.option_text_edit = QLineEdit(current_option, self)

        mlayout = QHBoxLayout()
        mlayout.addWidget(label)
        mlayout.addWidget(self.option_text_edit)
        self.setLayout(mlayout)

    def validate(self):
        curr_option = self.option_text_edit.text()
        if self.validator and not self.validator(curr_option):
            self.option_text_edit.setStyleSheet('border: 1px solid red;')
            return False
        return True

    def get_current_option(self):
        return self._convert(self.option_text_edit.text())


class OptionsWidget(QWidget):

    def __init__(self, all_options, current_options, parent=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        if not isinstance(all_options, dict):
            raise TypeError('Invalid option type, need dictionary, got {} instead.'.format(type(all_options)))
        if not isinstance(current_options, dict):
            raise TypeError('Invalid option type, need dictionary, got {} instead.'.format(type(all_options)))

        self.options = []

        self.threads_per_page = OptionItemComboBox('threads_per_page', 'Threads per page', all_options['threads_per_page'], current_options['threads_per_page'], self)
        self.options.append(self.threads_per_page)
        self.contacts_per_page = OptionItemComboBox('contacts_per_page', 'Contacts per page', all_options['contacts_per_page'], current_options['contacts_per_page'], self)
        self.options.append(self.contacts_per_page)
        self.messages_per_page = OptionItemComboBox('messages_per_page', 'Messages per page', all_options['messages_per_page'], current_options['messages_per_page'], self)
        self.options.append(self.messages_per_page)
        self.font_size = OptionItemTextEdit('font_size', 'Font size', current_options['font_size'], None, self)
        self.options.append(self.font_size)
        self.themes = OptionItemComboBox('theme', 'Theme', all_options['theme'], current_options['theme'], self)
        self.options.append(self.themes)

        mlayout = QVBoxLayout()
        mlayout.addWidget(self.threads_per_page)
        mlayout.addWidget(self.contacts_per_page)
        mlayout.addWidget(self.messages_per_page)
        mlayout.addWidget(self.font_size)
        mlayout.addWidget(self.themes)
        mlayout.addStretch(0)
        self.setLayout(mlayout)

    def get_options(self):
        response = {}
        for option in self.options:
            option.validate()
            response[option.name] = option.get_current_option()
        return response


if __name__ == '__main__':
    # test
    from icons import icons_rc
    import sys
    app = QApplication(sys.argv)
    b = PagedList('personal', (600, 400))
    b.show()
    app.exec_()
