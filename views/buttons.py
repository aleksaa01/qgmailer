from PyQt5.QtWidgets import QToolButton
from PyQt5.QtCore import QPropertyAnimation, pyqtProperty


class AnimatedCheckButton(QToolButton):

    def __init__(self, on_tick_func, anim_start=0, anim_end=255, anim_duration=300, parent=None):
        super().__init__(parent=parent)
        self.setCheckable(True)
        self._opacity = 0
        self.anim_start = anim_start
        self.anim_end = anim_end
        self.anim_duration = anim_duration

        self.anim = QPropertyAnimation(self, b'opacity')
        self.anim.setDuration(anim_duration)
        self.anim.setStartValue(anim_start)
        self.anim.setEndValue(anim_end)

        self.on_tick = on_tick_func

    def set_anim_start(self, val):
        self.anim_start = val
        self.anim.setStartValue(val)

    def set_anim_end(self, val):
        self.anim_end = val
        self.anim.setEndValue(val)

    def set_anim_duration(self, val):
        self.anim_duration = val
        self.anim.setDuration(val)

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
            self.anim.setEndValue(self.anim_end)
            self.anim.start()

        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.isChecked() is False:
            self.anim.stop()
            self.anim.setStartValue(self.anim.currentValue())
            self.anim.setEndValue(self.anim_start)
            self.anim.start()

        super().leaveEvent(event)

    def set_checked(self, checked):
        self.setChecked(checked)
        self.anim.stop()
        self.anim.setStartValue(self.anim.currentValue())
        if checked:
            self.anim.setEndValue(self.anim_end)
        else:
            self.anim.setEndValue(self.anim_start)
        self.anim.start()
