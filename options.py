from views.stylesheets import themes

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
        self.options = None
        self.filepath = filepath

        self.app_options = None
        self.all_options = None

        if load:
            self.load()

    def load(self, s=None):
        #FIXME: There is no need for options to stay in memory. It is not needed.
        if s:
            self.options = json.loads(s)
        else:
            self.options = json.load(open(self.filepath, 'r'))

        self.app_options = self.options['app_options']
        self.all_options = self.options['all_options']

    def current_value(self, option_name):
        return self.app_options[option_name]

    def change_option(self, name, value):
        self.app_options[name] = value

    def save(self):
        with open(self.filepath, 'w') as f:
            json.dump(
                {'app_options': self.app_options, 'all_options': self.all_options},
                f
            )
        self.optionsChanged.emit()

    def extract_theme(self, name=None):
        theme_name = name if name else self.app_options['theme']
        print('Extracting theme:', theme_name)

        return themes[theme_name]


if __name__ != '__main__':
    # TODO: Make Options all lowercase
    Options = JsonOptions()
