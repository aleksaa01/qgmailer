from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSizePolicy, \
    QWidget, QApplication, QScrollArea
from PyQt5.QtCore import QSize, pyqtSignal, QRect, Qt, QTimer, QPropertyAnimation, pyqtProperty, \
    QParallelAnimationGroup, QRectF
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPainter, QFontMetrics, QFont, QPainterPath

from qmodels.options import options
from channels.event_channels import OptionEventChannel, EmailEventChannel
from views.buttons import AnimatedCheckButton
from googleapis.gmail.labels import *


SCROLL_AREA_STYLESHEET = """
    QAbstractScrollArea{
        border: 0;
        border-top: 1px solid #455364;
        border-bottom: 1px solid #455364;
        border-radius: 0;
        padding: 0;
    }
    QScrollBar:vertical{
        background-color: transparent;
        width: 4px;
        margin: 2px 0px 2px 0px;
        border: 0;
        border-radius: 1px;
    }
    QScrollBar::add-line:vertical {
        border: none;
        background: none;
        width: 0;
        height: 0;
    }
    QScrollBar::sub-line:vertical {
        border: none;
        background: none;
        width: 0;
        height: 0;
    }
"""


# TODO: Add the ability to set item's icon color. You have to make sure that colors don't get changed
#  on theme change.
class Sidebar(QFrame):
    on_select = pyqtSignal(int)
    on_item_pressed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_item = None
        self._next_widget_id = 0
        # Instead of popping, put None in indecies of deleted items.
        # This is fine if we don't intend to continuously add/remove lots of items.
        # And it's cheap because it's a list of pointers.
        self.items = []

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.setFixedWidth(250)

    def add_item(self, name, image_path):
        item = SidebarItem(name, QPixmap(image_path))
        self.layout.addWidget(item)
        item_id = self._next_widget_id
        self._next_widget_id += 1
        self.items.append(item)
        item.on_pressed.connect(lambda _: self.item_pressed(item_id))
        return item_id

    def add_group(self, group_name, max_height=400):
        self.layout.addWidget(QLabel(f"<b>{group_name}</b>"), alignment=Qt.AlignHCenter)
        group = QWidget()
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(0)
        group.setLayout(group_layout)
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet(SCROLL_AREA_STYLESHEET)
        scroll_area.setWidgetResizable(True)
        scroll_area.setViewportMargins(0, 0, 0, 0)
        scroll_area.setWidget(group)
        scroll_area.setMaximumHeight(max_height)
        self.layout.addWidget(scroll_area)

        group_id = self._next_widget_id
        self._next_widget_id += 1
        self.items.append(group_layout)
        return group_id

    def add_item_to_group(self, group_id, item_name, item_image_path):
        item = SidebarItem(item_name, QPixmap(item_image_path))
        item_id = self._next_widget_id
        self._next_widget_id += 1
        self.items.append(item)
        item.on_pressed.connect(lambda _: self.item_pressed(item_id))
        group_layout = self.items[group_id]
        group_layout.addWidget(item)
        group_layout.update()

        return item_id

    def add_stretch(self):
        self.layout.addStretch(1)

    def remove_item(self, item_id, group_id=None):
        item = self.items[item_id]
        if self.current_item == item:
            item.set_checked(False)
            self.current_item = None

        if group_id:
            parent_layout = self.item[group_id]
        else:
            parent_layout = self.layout

        item_idx = parent_layout.indexOf(item)
        assert item_idx != -1
        layout_item = parent_layout.takeAt(item_idx)
        layout_item.widget().serParent(None)
        del layout_item

        self.items[item_id] = None
        # TODO: Test if this is necessary at all.
        self.update()

    def change_item_name(self, item_id, new_name):
        item = self.items[item_id]
        item.text = new_name
        # TODO: Is this even needed ?
        self.update()

    def item_pressed(self, widget_id):
        item = self.items[widget_id]
        if self.current_item:
            self.current_item.set_checked(False)
        self.current_item = item
        item.set_checked(True)
        self.on_item_pressed.emit(widget_id)

    def select_item(self, widget_id):
        if widget_id is None:
            if self.current_item:
                self.current_item.set_checked(False)
            self.current_item = None
        else:
            item = self.items[widget_id]
            if self.current_item:
                self.current_item.set_checked(False)
            self.current_item = item
            item.set_checked(True)


class SidebarItem(QWidget):
    on_pressed = pyqtSignal(bool)

    def __init__(self, text, pixmap=None, parent=None):
        super().__init__(parent)

        rgb_value = 255 if options.theme == 'dark' else 0
        self.theme = options.theme

        # You are supposed to set size policy like this, and not to override sizePolicy()
        # If vertical policy was preferred, then you would have to implement minimumSizeHint and
        # maximumSize to limit how much the item can shrink and grow.
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self.text = text
        self.pixmap = pixmap
        self._prepare_pixmap(QColor(rgb_value, rgb_value, rgb_value, 200))
        self.spacing = 12
        self.font = QApplication.font()
        self.font.setBold(True)
        self.fm = QFontMetrics(self.font)
        self.mouse_over = False
        self.checked = False
        self.active = False
        self.setMouseTracking(True)

        self.background_color = QColor(rgb_value, rgb_value, rgb_value, 0)
        self.background_animation = QPropertyAnimation(self, b'opacity')
        self.background_animation.setStartValue(0)
        self.background_animation.setEndValue(40)
        self.background_animation.setDuration(300)

        self.indicator_pos = 5
        self.indicator_position_anim = QPropertyAnimation(self, b'indicator_position')
        self.indicator_position_anim.setStartValue(5)
        self.indicator_position_anim.setEndValue(-5)
        self.indicator_position_anim.setDuration(300)

        self.indicator_background = QColor(rgb_value, rgb_value, rgb_value, 0)
        self.indicator_opacity_anim = QPropertyAnimation(self, b'indicator_opacity')
        self.indicator_opacity_anim.setStartValue(0)
        self.indicator_opacity_anim.setEndValue(140)
        self.indicator_opacity_anim.setDuration(300)

        self.all_animations = QParallelAnimationGroup()
        self.all_animations.addAnimation(self.background_animation)
        self.all_animations.addAnimation(self.indicator_position_anim)
        self.all_animations.addAnimation(self.indicator_opacity_anim)

        OptionEventChannel.subscribe('theme', self.handle_theme_change)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.on_pressed.emit(True)

    def set_checked(self, checked):
        self.checked = checked
        self.check_active()

    def check_active(self):
        old_active = self.active
        if self.checked:
            self.active = True
        else:
            self.active = self.mouse_over

        if old_active == self.active:
            return

        if self.active is True:
            self.all_animations.setDirection(QParallelAnimationGroup.Forward)
            self.all_animations.start()
        else:
            self.all_animations.setDirection(QParallelAnimationGroup.Backward)
            self.all_animations.start()

        # Calling update 10 times will result in only one update.
        # So it's fine to do this even after starting the animations.
        self.update()

    def enterEvent(self, event):
        self.mouse_over = True
        self.check_active()

    def leaveEvent(self, event):
        self.mouse_over = False
        self.check_active()

    def sizeHint(self):
        # sizeHint is used by layouts to get the recommended size of the widget.
        return QSize(100, 40)

    # def minimumSizeHint(self):
    #     # minimumSizeHint is used by layouts to get the minimum size of the widget.
    #     # It's ignored if minimumSize is also implemented
    #     return self.sizeHint()

    def paintEvent(self, paint_event):
        super().paintEvent(paint_event)
        widget_rect = self.rect()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(widget_rect, self.background_color)

        if self.mouse_over:
            indicator_rect = QRect(
                widget_rect.width() + self.indicator_pos - 6, (widget_rect.height() - 6) // 2, 6, 9
            )
            triangle_path = QPainterPath(indicator_rect.topRight())
            triangle_path.lineTo(indicator_rect.bottomRight())
            mid_left = indicator_rect.bottomLeft()
            mid_left.setY(mid_left.y() - indicator_rect.height() // 2)
            triangle_path.lineTo(mid_left)
            triangle_path.lineTo(indicator_rect.topRight())

            painter.fillPath(triangle_path, self.indicator_background)

        if self.pixmap:
            pixmap_rect = QRect(self.spacing, (widget_rect.height() - 20) // 2, 20, 20)
            painter.drawPixmap(pixmap_rect, self.pixmap, self.pixmap.rect())
            # painter.drawRect(pixmap_rect)
        else:
            pixmap_rect = QRect(0, 0, 0, 0)

        text_rect = QRect(pixmap_rect.right() + self.spacing, 0, 0, widget_rect.height())
        text_rect.setWidth(widget_rect.width() - text_rect.left())
        # painter.drawRect(text_rect)

        text = self.fm.elidedText(self.text, Qt.ElideRight, text_rect.width())
        painter.setFont(self.font)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, text)

    def _prepare_pixmap(self, qcolor):
        if self.pixmap is None:
            return
        painter = QPainter(self.pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
        painter.fillRect(self.pixmap.rect(), qcolor)
        painter.end()

    def _get_opacity(self):
        return self.background_color.alpha()

    def _set_opacity(self, new_value):
        self.background_color.setAlpha(new_value)
        self.update()

    opacity = pyqtProperty('int', _get_opacity, _set_opacity)

    def _get_indicator_position(self):
        return self.indicator_pos

    def _set_indicator_position(self, new_value):
        self.indicator_pos = new_value
        self.update()

    indicator_position = pyqtProperty('int', _get_indicator_position, _set_indicator_position)

    def _get_indicator_opacity(self):
        return self.indicator_background.alpha()

    def _set_indicator_opacity(self, new_value):
        self.indicator_background.setAlpha(new_value)
        self.update()

    indicator_opacity = pyqtProperty('int', _get_indicator_opacity, _set_indicator_opacity)

    def handle_theme_change(self, theme):
        if theme == self.theme:
            return

        self.theme = theme
        if theme == 'dark':
            rgb_value = 255
        else:
            rgb_value = 0

        self.background_color.setRgb(
            rgb_value, rgb_value, rgb_value, self.background_color.alpha())
        self.indicator_background.setRgb(
            rgb_value, rgb_value, rgb_value, self.indicator_background.alpha())
        self._prepare_pixmap(QColor(rgb_value, rgb_value, rgb_value, 200))
        self.update()
