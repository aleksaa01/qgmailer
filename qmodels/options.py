import os
import json

from channels.event_channels import OptionEventChannel


PROJECT_CONFIG_FILE = 'config.json'
PROJECT_CONFIG_PATH = os.path.join(os.getcwd(), PROJECT_CONFIG_FILE)
APP_CONFIG_FILE = 'app_config.json'
APP_CONFIG_PATH = os.path.join(os.getcwd(), APP_CONFIG_FILE)


def save(func):
    def wrapper(self, *args, **kwargs):
        return_value = func(self, *args, **kwargs)
        self.save_config()
        return return_value
    return wrapper


class OptionModel(object):

    def __init__(self):

        self._all_emails_per_page = None
        self._emails_per_page = None
        self._all_contacts_per_page = None
        self._contacts_per_page = None
        self._font_size = None
        self._all_theme = None
        self._theme = None

        if not os.path.exists(APP_CONFIG_PATH):
            self._create_app_config()

        self._load()

    def _create_app_config(self):
        with open(PROJECT_CONFIG_PATH, 'r') as project_file:
            with open(APP_CONFIG_PATH, 'w') as app_file:
                json.dump(json.load(project_file), app_file)

    def _load(self):
        with open(APP_CONFIG_PATH) as fp:
            data = json.load(fp)
            self._all_emails_per_page = [str(opt) for opt in data['possible_options']['emails_per_page']]
            self._emails_per_page = str(data['app_options']['emails_per_page'])
            self._all_contacts_per_page = [str(opt) for opt in data['possible_options']['contacts_per_page']]
            self._contacts_per_page = str(data['app_options']['contacts_per_page'])
            self._font_size = str(data['app_options']['font_size'])
            self._all_theme = [str(opt) for opt in data['possible_options']['theme']]
            self._theme = str(data['app_options']['theme'])

    def save_config(self):
        print('saving options...')
        with open(APP_CONFIG_PATH) as fp:
            data = json.load(fp)
            data['app_options']['emails_per_page'] = self._emails_per_page
            data['app_options']['contacts_per_page'] = self._contacts_per_page
            data['app_options']['font_size'] = self._font_size
            data['app_options']['theme'] = self._theme
        with open(APP_CONFIG_PATH, 'w') as fp:
            json.dump(data, fp)

    @property
    def all_emails_per_page(self):
        return self._all_emails_per_page

    @property
    def emails_per_page(self):
        return self._emails_per_page

    @emails_per_page.setter
    @save
    def emails_per_page(self, value):
        self._emails_per_page = value

    @property
    def all_contacts_per_page(self):
        return self._all_contacts_per_page

    @property
    def contacts_per_page(self):
        return self._contacts_per_page

    @contacts_per_page.setter
    @save
    def contacts_per_page(self, value):
        self._contacts_per_page = value

    @property
    def font_size(self):
        return self._font_size

    @font_size.setter
    @save
    def font_size(self, value):
        self._font_size = value

    @property
    def all_theme(self):
        return self._all_theme

    @property
    def theme(self):
        return self._theme

    @theme.setter
    @save
    def theme(self, value):
        self._theme = value

options = OptionModel()
