from PyQt5.QtWidgets import QToolButton
from PyQt5.QtCore import QPropertyAnimation, pyqtProperty


class AnimatedCheckButton(QToolButton):

    def __init__(self, on_tick_func, parent=None):
        super().__init__(parent=parent)
        self.setCheckable(True)
        self._opacity = 0
        self.anim = QPropertyAnimation(self, b'opacity')
        self.anim.setDuration(300)
        self.anim.setStartValue(0)
        self.anim.setEndValue(255)

        self.on_tick = on_tick_func

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, value):
        self._opacity = value
        if value != 1:
            self.on_tick(self, value)

    opacity = pyqtProperty('int', get_opacity, set_opacity)

    def enterEvent(self, event):
        if self.isChecked() is False:
            self.anim.stop()
            self.anim.setStartValue(self.anim.currentValue())
            self.anim.setEndValue(255)
            self.anim.start()

        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.isChecked() is False:
            self.anim.stop()
            self.anim.setStartValue(self.anim.currentValue())
            self.anim.setEndValue(0)
            self.anim.start()

        super().leaveEvent(event)

    def set_checked(self, checked):
        self.setChecked(checked)
        self.anim.stop()
        self.anim.setStartValue(self.anim.currentValue())
        if checked:
            self.anim.setEndValue(255)
        else:
            self.anim.setEndValue(0)
        self.anim.start()
