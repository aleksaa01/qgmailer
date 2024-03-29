from PyQt5.QtWidgets import QStyledItemDelegate, QApplication
from PyQt5.QtCore import QSize, Qt, QRect
from PyQt5.QtGui import QFontMetrics

from channels.event_channels import OptionEventChannel
from qmodels.email import EmailRole
from qmodels.options import options

from googleapis.gmail.labels import GMAIL_LABEL_SENT


class EmailDelegate(QStyledItemDelegate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.font = QApplication.font()
        self.font_bold = QApplication.font()
        self.font.setPixelSize(options.font_size)
        self.font_bold.setPixelSize(options.font_size)
        self.font_bold.setBold(True)
        self.fm = QFontMetrics(self.font)
        self.fm_bold = QFontMetrics(self.font_bold)

        # This should be set by the view. Indicates whether we should draw wide or narrow items.
        self.wide_items = False
        OptionEventChannel.subscribe('font_size', self.update_font)

    def update_font(self, font_size):
        self.font.setPixelSize(font_size)
        self.font_bold.setPixelSize(font_size)
        self.fm = QFontMetrics(self.font)
        self.fm_bold = QFontMetrics(self.font_bold)

    def sizeHint(self, option, index):
        if self.wide_items:
            return QSize(option.rect.width(), self.fm.height() * 3 + 40)
        else:
            return QSize(option.rect.width(), self.fm.height() + 24)

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        if self.wide_items:
            self.paint_wide_item(painter, option, index)
        else:
            self.paint_narrow_item(painter, option, index)

    def item_data(self, index):
        email = index.data(EmailRole)
        return ((email.get('field_from') or "DoNotReply"), email.get('subject'),
                email.get('snippet'), email.get('date'), email.get('unread'))

    def paint_wide_item(self, painter, option, index):
        painter.save()
        font = self.font
        fm = self.fm

        email_field, subject, snippet, date, unread = self.item_data(index)
        
        # If email is unread paint certain parts bold, if not then just set font_bold and fm_bold
        # to font and fm to avoid unnecessary checks later.
        if unread is False:
            font_bold = font
            fm_bold = fm
        else:
            font_bold = self.font_bold
            fm_bold = self.fm_bold
        option_rect = option.rect
        option_rect.setX(10)
        option_rect.setY(option_rect.y() + 10)
        row_height = (option_rect.height()) // 3
        option_rect.setWidth(option_rect.width() - 10)
        viewport_width = option_rect.width()

        email_field_rect = QRect(*option_rect.getRect())
        email_field_rect.setHeight(row_height)
        email_field_width = viewport_width // 2
        email_field_rect.setWidth(email_field_width)
        #email_field = fm_bold.elidedText(email_field, Qt.ElideRigth, email_field_width)
        painter.setFont(font_bold)
        painter.drawText(email_field_rect, 0, email_field)

        date_rect = QRect(*option_rect.getRect())
        date_rect.setHeight(row_height)
        date_rect.setLeft(email_field_rect.right())
        date_width = viewport_width // 2
        date_rect.setWidth(date_width)
        #date = fm_bold.elidedText(date, Qt.ElideLeft, date_width)
        painter.drawText(date_rect, Qt.AlignRight, date)

        subject_rect = QRect(*option_rect.getRect())
        subject_rect.setTop(email_field_rect.bottom())
        subject_rect.setHeight(row_height)
        subject_width = min(fm_bold.horizontalAdvance(subject), viewport_width)
        subject = fm_bold.elidedText(subject, Qt.ElideRight, subject_width)
        painter.drawText(subject_rect, 0, subject)

        snippet_rect = QRect(*option_rect.getRect())
        snippet_rect.setTop(subject_rect.bottom())
        snippet_rect.setHeight(row_height)
        snippet_rect.setWidth(viewport_width)
        snippet_width = min(fm.horizontalAdvance(snippet), viewport_width)
        snippet = fm.elidedText(snippet, Qt.ElideRight, snippet_width)
        painter.setFont(font)
        painter.drawText(snippet_rect, 0, snippet)

        painter.restore()

    def paint_narrow_item(self, painter, option, index):
        painter.save()
        font = self.font
        fm = self.fm

        email_field, subject, snippet, date, unread = self.item_data(index)

        # If email is unread paint certain parts bold, if not then just set font_bold and fm_bold
        # to font and fm to avoid unnecessary checks later.
        if unread is False:
            font_bold = font
            fm_bold = fm
        else:
            font_bold = self.font_bold
            fm_bold = self.fm_bold
        option_rect = option.rect
        option_rect.setY(option_rect.y() + (option_rect.height() - fm.height()) // 2)
        option_rect.setX(10)
        viewport_width = option_rect.width()

        email_field_rect = QRect(*option_rect.getRect())
        email_field_width = min(200, viewport_width)
        email_field_rect.setWidth(email_field_width)
        email_field = fm_bold.elidedText(email_field, Qt.ElideRight, email_field_width)
        painter.setFont(font_bold)
        painter.drawText(email_field_rect, 0, email_field)
        viewport_width -= email_field_width

        date_rect = QRect(*option_rect.getRect())
        date_width = min(max(fm_bold.horizontalAdvance(date), 100), viewport_width)
        viewport_width -= date_width

        subject_rect = QRect(*option_rect.getRect())
        subject_rect.setLeft(email_field_rect.right())
        subject_width = min(max(fm_bold.horizontalAdvance(subject), 10), viewport_width)
        subject_rect.setWidth(subject_width)
        subject = fm_bold.elidedText(subject, Qt.ElideRight, subject_width)
        painter.drawText(subject_rect, 0, subject)
        viewport_width -= subject_width

        if viewport_width > 0 and snippet:
            snippet_rect = QRect(*option_rect.getRect())
            snippet_rect.setLeft(subject_rect.right())
            snippet_width = viewport_width
            snippet_rect.setWidth(snippet_width)
            snippet = fm.elidedText(' - ' + snippet, Qt.ElideRight, snippet_width)
            painter.setFont(font)
            painter.drawText(snippet_rect, 0, snippet)

        date_rect.setLeft(option_rect.width() - date_width)
        date_rect.setWidth(date_width)
        painter.setFont(font_bold)
        painter.drawText(date_rect, Qt.AlignRight, date)

        painter.restore()


class SentEmailDelegate(EmailDelegate):

    def item_data(self, index):
        email = index.data(EmailRole)
        return (email.get('field_to'), email.get('subject'), email.get('snippet'),
                email.get('date'), email.get('unread'))


class TrashEmailDelegate(EmailDelegate):

    def item_data(self, index):
        email = index.data(EmailRole)
        if GMAIL_LABEL_SENT in email.get('label_ids'):
            email_field = 'To: ' + email.get('field_to')
        else:
            email_field = 'From: ' + (email.get('field_from') or "DoNotReply")
        return (email_field, email.get('subject'), email.get('snippet'),
                email.get('date'), email.get('unread'))
