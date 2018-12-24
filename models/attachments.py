from PySide2.QtCore import QAbstractListModel, Qt
from PySide2.QtGui import QPixmap
import os


IMAGES_PATH = os.path.join(os.getcwd(), 'views', 'icons', 'images')


class AttachmentListModel(QAbstractListModel):

    FILE_TYPE_TO_IMG = {
        '.doc': 'word_file.png', '.docx': 'word_file.png',
        '.ppt': 'powerpoint_file.png', '.pptx': 'powerpoint_file.png',
        '.xls': 'excel_file.png', '.xlsx': 'excel_file.png',
        '.txt': 'text_file.png',
        '.jpg': 'jpg_file.png', '.jpeg': 'jpg_file.png',
        '.png': 'png_file.png'
    }

    UNKNOWN_TO_IMG = 'unknown_file.png'

    def __init__(self, attachments=None, parent=None):
        """
        :param attachments: list of dictionaries with keys:
        (filename, payload, binary, mail_content_type, content_id, content_transfer_encoding)
        :param parent: Parent widget.
        """
        super().__init__(parent)

        self._attachments = [] if attachments is None else attachments

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
            img_filename = self.FILE_TYPE_TO_IMG.get(extension, None)
            if img_filename is None:
                img_filename = self.UNKNOWN_TO_IMG

            filepath = os.path.join(IMAGES_PATH, img_filename)
            pix = QPixmap(filepath)
            return pix

    def extractPayload(self, index):
        return self._attachments[index.row()]['payload']

    def extractFilename(self, index):
        return self._attachments[index.row()]['filename']

    def checkData(self):
        if self._attachments:
            return True
        return False

    def addData(self, attachments):
        self.beginResetModel()
        self._attachments += attachments
        self.endResetModel()

    def replaceData(self, attachments):
        self.beginResetModel()
        self._attachments = attachments
        self.endResetModel()

    def clearData(self):
        self.beginResetModel()
        self._attachments.clear()
        self.endResetModel()
