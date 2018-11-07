from views.stylesheets import themes

from configparser import ConfigParser
from ast import literal_eval
import os
import json

PROJECT_CONFIG_FILE = 'config.json'
PROJECT_CONFIG_PATH = os.path.join(os.getcwd(), PROJECT_CONFIG_FILE)
APP_CONFIG_FILE = 'app_config.json'
APP_CONFIG_PATH = os.path.join(os.getcwd(), APP_CONFIG_FILE)


def create_app_config2():
    with open(PROJECT_CONFIG_PATH, 'r') as pf:
        with open(APP_CONFIG_FILE, 'w') as af:
            af.write(pf.read())
    print('Configuration file for the application is created.')

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



class DefaultOptions(object):
    """
    This class should be instantiated only once, and used as a Singleton.
    Module variables can be used instead of a class Singletons.
    Just assign the instance of this class to a module variable and then import
    that module variable where ever you need it.
    """

    def __init__(self, filepath=APP_CONFIG_PATH, load=True):
        self.config = ConfigParser()
        self.filepath = filepath

        self.section_default = 'APPLICATION_DEFAULTS'
        self.section_current = self.section_default
        self.section_app_options = 'APPLICATION_DEFAULTS'
        self.section_all_options = 'ALL_OPTIONS'
        self.theme_current = 'default'

        if load:
            self.load()

    def load(self, s=None):
        if s is None:
            self.config.read_file(open(self.filepath))
        else:
            self.config.read_string(s)
        print('Options loaded')

    def set_section(self, section):
        if self.config.has_section(section):
            self.section_current = section
        else:
            print(self.config.sections())
            raise ValueError('Section: "{}" doesn\'t exist'.format(section))

    def set_default_section(self):
        self.set_section(self.section_default)

    def sections(self):
        return self.config.sections()

    def options(self, section):
        maped_options = {}
        for option in self.config.options(section):
            maped_options[option] = literal_eval(self.config[section][option])
        return maped_options

    def set_path(self, new_path):
        self.filepath = new_path

    def extract_option(self, name, section=None):
        current_section = self.section_current
        if section:
            current_section = section

        return literal_eval(self.config[current_section][name])

    def change_option(self, name, value, save=True):
        if type(value) != str:
            value = str(value)
        self.config[self.section_current][name] = value

        if save:
            self.save()

    def save(self):
        self.config.write(open(self.filepath, 'w'))

    def app_options(self):
        return self.options(self.section_app_options)

    def all_options(self):
        return self.options(self.section_all_options)

    def themes(self):
        return list(themes.keys())

    def extract_theme(self, name=None):
        print('extracting theme!')
        if name is None:
            return themes[self.theme_current]
        return themes[name]


if __name__ != '__main__':
    Options = JsonOptions()
