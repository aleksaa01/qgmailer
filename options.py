from views.stylesheets import themes

from configparser import ConfigParser
from ast import literal_eval
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
        self.options = None
        self.filepath = filepath

        self.app_options = None
        self.all_options = None

        if load:
            self.load()

    def load(self, s=None):
        if s:
            self.options = json.loads(s)
            return
        self.options = json.load(open(self.filepath, 'r'))
        self.app_options = self.options['app_options']
        self.all_options = self.options['all_options']

    def change_option(self, name, value, save=True):
        self.app_options[name] = value
        if save:
            self.save()

    def save(self):
        print(self.options)
        with open(self.filepath, 'w') as f:
            json.dump(
                {'app_options': self.app_options, 'all_options': self.all_options},
                f
            )

    def extract_theme(self, name=None):
        print('extracting theme!')
        if name is None:
            return themes[self.app_options['theme']]
        return themes[name]


if __name__ != '__main__':
    Options = JsonOptions()
