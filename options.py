from PyQt5.QtCore import QObject, pyqtSignal
import os
import json

PROJECT_CONFIG_FILE = 'config.json'
PROJECT_CONFIG_PATH = os.path.join(os.getcwd(), PROJECT_CONFIG_FILE)
APP_CONFIG_FILE = 'app_config.json'
APP_CONFIG_PATH = os.path.join(os.getcwd(), APP_CONFIG_FILE)


def create_app_config():
    with open(PROJECT_CONFIG_PATH, 'r') as project_file:
        with open(APP_CONFIG_PATH, 'w') as app_file:
            json.dump(json.load(project_file), app_file)


if not os.path.exists(APP_CONFIG_PATH):
    create_app_config()


class JsonOptions(QObject):
    optionsChanged = pyqtSignal()
    """
    all_options always stay the same, while app_options can be changed
    """

    def __init__(self, filepath=APP_CONFIG_PATH, load=True):
        super().__init__(None)
        self._options = None
        self.filepath = filepath

        self._app_options = None
        self._all_options = None

        if load:
            self.load()

    def load(self, s=None):
        #FIXME: There is no need for options to stay in memory. It is not needed.
        if s:
            self._options = json.loads(s)
        else:
            self._options = json.load(open(self.filepath, 'r'))

        self._app_options = self._options['app_options']
        self._possible_options = self._options['possible_options']

    def current_value(self, option_name):
        return self._app_options[option_name]

    def change_option(self, name, value):
        self._app_options[name] = value

    def current_options(self):
        return self._app_options

    def save(self):
        with open(self.filepath, 'w') as f:
            json.dump(
                {'_app_options': self._app_options, 'all_options': self._possible_options},
                f
            )
        self.optionsChanged.emit()


if __name__ != '__main__':
    # TODO: Make Options all lowercase
    Options = JsonOptions()
