from PyQt5.QtCore import pyqtSignal

from options import Options
from viewmodels_mvvm._singleton import SingletonViewModel

import weakref


class OptionsViewModel(object, metaclass=SingletonViewModel):

    def __init__(self):
        self._options = Options
        self._current_theme = None

        self._callbacks = []

        self._options.optionsChanged.connect(self.notify)

    def run(self):
        return

    def change_option(self, name, value, save=True):
        self._options.change_option(name, value, save)

    def replace_options(self, new_options):
        self._options.app_options = new_options
        self._options.save()

    @property
    def current_theme(self):
        return self._current_theme

    @current_theme.setter
    def current_theme(self, name):
        self._current_theme = self._options.extract_theme(name)
        return self._current_theme

    def extract_theme(self):
        return self._options.extract_theme(self.current_theme)

    def all_options(self):
        return self._options.all_options

    def current_options(self):
        return self._options.app_options

    def register(self, callback):
        self._callbacks.append(callback)

    def notify(self):
        for callback in self._callbacks:
            callback()