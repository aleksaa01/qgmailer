from PyQt5.QtCore import QAbstractListModel, Qt
from PyQt5.QtGui import QPixmap
import os


IMAGES_PATH = os.path.join(os.getcwd(), 'views', 'icons', 'images')


class AttachmentListModel(QAbstractListModel):

    EXT_TO_IMG = {
        '.doc': 'word_file.png', '.docx': 'word_file.png',
        '.ppt': 'powerpoint_file.png', '.pptx': 'powerpoint_file.png',
        '.xls': 'excel_file.png', '.xlsx': 'excel_file.png',
        '.txt': 'text_file.png',
        '.jpg': 'jpg_file.png', '.jpeg': 'jpg_file.png',
        '.png': 'png_file.png'
    }

    UNKNOWN_EXT = 'unknown_file.png'

    def __init__(self, attachments=None, parent=None):
        """
        :param attachments: list of dictionaries with keys:
        (filename, payload, binary, mail_content_type, content_id, content_transfer_encoding)
        :param parent: Parent widget.
        """
        super().__init__(parent)

        self._attachments = [] if attachments is None else attachments
        self.pixmap_cache = {}

    def rowCount(self, parent=None):
        return len(self._attachments)

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def data(self, index, role=None):
        if role == Qt.DisplayRole:
            return self._attachments[index.row()]['filename']

        # consider caching pixmaps for time saving
        elif role == Qt.DecorationRole:
            extension = os.path.splitext(self._attachments[index.row()]['filename'])[1].lower()
            img_file = self.EXT_TO_IMG.get(extension, None)
            if img_file is None:
                img_file = self.UNKNOWN_EXT

            pixmap = self.pixmap_cache.get(img_file)
            if pixmap is None:
                pixmap = QPixmap(f':/images/{img_file}')
                self.pixmap_cache[img_file] = pixmap

            return pixmap

    def emit_attachments(self, index):
        return self._attachments[index.row()]['payload']

    def emit_filename(self, index):
        return self._attachments[index.row()]['filename']

    def add_data(self, attachments):
        self.beginResetModel()
        self._attachments += attachments
        self.endResetModel()

    def replace_data(self, attachments):
        self.beginResetModel()
        self._attachments = attachments
        self.endResetModel()

    def clear_data(self):
        self.beginResetModel()
        self._attachments.clear()
        self.endResetModel()

    def __len__(self):
        return len(self._attachments)
