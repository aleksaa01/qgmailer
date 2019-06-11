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


class JsonOptions(object):
    """
    all_options always stay the same, while app_options can be changed
    """

    def __init__(self, filepath=APP_CONFIG_PATH, load=True):
        self._filepath = filepath

        self._app_options = None
        self._all_options = None

        if load:
            self.load()

    def load(self, s=None):
        if s:
            options = json.loads(s)
        else:
            options = json.load(open(self._filepath, 'r'))

        self._app_options = options['app_options']
        self._possible_options = options['possible_options']

    def change_option(self, name, value):
        self._app_options[name] = value

    def current_options(self):
        return self._app_options

    def possible_options(self):
        return self._possible_options

    def save(self):
        with open(self._filepath, 'w') as f:
            json.dump(
                {'app_options': self._app_options, 'possible_options': self._possible_options},
                f
            )


if __name__ != '__main__':
    # TODO: Make Options all lowercase
    Options = JsonOptions()
