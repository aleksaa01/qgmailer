from PyQt5.QtCore import pyqtSignal

from options import Options
from viewmodels_mvvm._singleton import SingletonViewModel


class OptionsViewModel(object, metaclass=SingletonViewModel):

    optionsChanged = pyqtSignal()

    def __init__(self):
        self._options = Options
        self._current_theme = None

    def change_option(self, name, value, save=True):
        self._options.change_option(name, value, save)

    @property
    def current_theme(self):
        return self._current_theme

    @current_theme.setter
    def current_theme(self, name):
        self._current_theme = self._options.extract_theme(name)
        return self._current_theme

    def all_options(self):
        return self._options.all_options

    def current_options(self):
        return self._options.app_options