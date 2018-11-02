from configparser import ConfigParser
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

    def __init__(self, filepath=DEFAULT_FILEPATH, load_later=False):
        self.config = ConfigParser()
        self.filepath = filepath

        self.current_section = 'DEFAULT'

        if load_later is False:
            self.load()

    def load(self, s=None):
        if s is None:
            self.config.read_file(open(self.filepath))
        else:
            self.config.read_string(s)
        print('Options loaded')

    def set_section(self, section):
        if self.config.has_section(section):
            self.current_section = section
        else:
            print(self.config.sections())
            raise ValueError('Section: "{}" doesn\'t exist'.format(section))

    def set_path(self, new_path):
        self.filepath = new_path

    def __getattr__(self, name):
        return self.config[self.current_section][name]

    def change_option(self, name, value):
        if type(value) != str:
            value = str(value)
        self.config[self.current_section][name] = value
        self.save()

    def save(self):
        self.config.write(open(self.filepath, 'w'))


if __name__ != '__main__':
    Options = DefaultOptions()
