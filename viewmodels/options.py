from options import Options
from viewmodels._singleton import SingletonViewModel


class OptionsViewModel(object, metaclass=SingletonViewModel):

    def __init__(self):
        self._options = Options

        self._callbacks = []

        self._options.optionsChanged.connect(self.notify)

    def run(self):
        return

    def change_option(self, name, value, save=True):
        self._options.change_option(name, value, save)

    def replace_options(self, new_options):
        self._options.app_options = new_options
        self._options.save()
        self.notify()

    def extract_theme(self, theme_name=None):
        return self._options.extract_theme(theme_name)

    def all_options(self):
        return self._options.all_options

    def current_options(self):
        return self._options.app_options

    def register(self, callback):
        self._callbacks.append(callback)

    def notify(self):
        for callback in self._callbacks:
            callback()
