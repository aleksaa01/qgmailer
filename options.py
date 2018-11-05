from configparser import ConfigParser
from ast import literal_eval
import os

DEFAULT_FILENAME = 'config.ini'
DEFAULT_FILEPATH = os.path.join(os.getcwd(), DEFAULT_FILENAME)


class DefaultOptions(object):
    """
    This class should be instantiated only once, and used as a Singleton.
    Module variables can be used instead of a class Singletons.
    Just assign the instance of this class to a module variable and then import
    that module variable where ever you need it.
    """

    def __init__(self, filepath=DEFAULT_FILEPATH, load=True):
        self.config = ConfigParser()
        self.filepath = filepath

        self.section_default = 'APPLICATION_DEFAULTS'
        self.section_current = self.section_default
        self.section_app_options = 'APPLICATION_DEFAULTS'
        self.section_all_options = 'ALL_OPTIONS'

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


if __name__ != '__main__':
    Options = DefaultOptions()
