import os
import json

from logs.loggers import default_logger

LOG = default_logger()


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

        self._personal_shortcut = None
        self._social_shortcut = None
        self._updates_shortcut = None
        self._promotions_shortcut = None
        self._forums_shortcut = None
        self._sent_shortcut = None
        self._unread_shortcut = None
        self._important_shortcut = None
        self._starred_shortcut = None
        self._trash_shortcut = None
        self._spam_shortcut = None
        self._send_email_shortcut = None
        self._contacts_shortcut = None
        self._settings_shortcut = None

        self._resolution = None

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
            self._all_emails_per_page = [opt for opt in data['possible_options']['emails_per_page']]
            self._emails_per_page = data['app_options']['emails_per_page']
            self._all_contacts_per_page = [opt for opt in data['possible_options']['contacts_per_page']]
            self._contacts_per_page = data['app_options']['contacts_per_page']
            self._font_size = data['app_options']['font_size']
            self._all_theme = [opt for opt in data['possible_options']['theme']]
            self._theme = data['app_options']['theme']

            self._personal_shortcut = data['app_options']['personal_shortcut']
            self._social_shortcut = data['app_options']['social_shortcut']
            self._updates_shortcut = data['app_options']['updates_shortcut']
            self._promotions_shortcut = data['app_options']['promotions_shortcut']
            self._forums_shortcut = data['app_options']['forums_shortcut']
            self._sent_shortcut = data['app_options']['sent_shortcut']
            self._unread_shortcut = data['app_options']['unread_shortcut']
            self._important_shortcut = data['app_options']['important_shortcut']
            self._starred_shortcut = data['app_options']['starred_shortcut']
            self._trash_shortcut = data['app_options']['trash_shortcut']
            self._spam_shortcut = data['app_options']['spam_shortcut']
            self._send_email_shortcut = data['app_options']['send_email_shortcut']
            self._contacts_shortcut = data['app_options']['contacts_shortcut']
            self._settings_shortcut = data['app_options']['settings_shortcut']


            self._resolution = data['app_options']['resolution']

    def save_config(self):
        LOG.info('saving options...')
        with open(APP_CONFIG_PATH) as fp:
            data = json.load(fp)
            data['app_options']['emails_per_page'] = self._emails_per_page
            data['app_options']['contacts_per_page'] = self._contacts_per_page
            data['app_options']['font_size'] = self._font_size
            data['app_options']['theme'] = self._theme

            data['app_options']['personal_shortcut'] = self._personal_shortcut
            data['app_options']['social_shortcut'] = self._social_shortcut
            data['app_options']['updates_shortcut'] = self._updates_shortcut
            data['app_options']['promotions_shortcut'] = self._promotions_shortcut
            data['app_options']['forums_shortcut'] = self._forums_shortcut
            data['app_options']['sent_shortcut'] = self._sent_shortcut
            data['app_options']['unread_shortcut'] = self._unread_shortcut
            data['app_options']['important_shortcut'] = self._important_shortcut
            data['app_options']['starred_shortcut'] = self._starred_shortcut
            data['app_options']['trash_shortcut'] = self._trash_shortcut
            data['app_options']['spam_shortcut'] = self._spam_shortcut
            data['app_options']['send_email_shortcut'] = self._send_email_shortcut
            data['app_options']['contacts_shortcut'] = self._contacts_shortcut
            data['app_options']['settings_shortcut'] = self._settings_shortcut


            data['app_options']['resolution'] = self._resolution
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

    @property
    def personal_shortcut(self):
        return self._personal_shortcut

    @personal_shortcut.setter
    @save
    def personal_shortcut(self, value):
        self._personal_shortcut = value

    @property
    def social_shortcut(self):
        return self._social_shortcut

    @social_shortcut.setter
    @save
    def social_shortcut(self, value):
        self._social_shortcut = value

    @property
    def updates_shortcut(self):
        return self._updates_shortcut

    @updates_shortcut.setter
    @save
    def updates_shortcut(self, value):
        self._updates_shortcut = value

    @property
    def promotions_shortcut(self):
        return self._promotions_shortcut

    @promotions_shortcut.setter
    @save
    def promotions_shortcut(self, value):
        self._promotions_shortcut = value

    @property
    def forums_shortcut(self):
        return self._forums_shortcut

    @forums_shortcut.setter
    @save
    def forums_shortcut(self, value):
        self._forums_shortcut = value

    @property
    def sent_shortcut(self):
        return self._sent_shortcut

    @sent_shortcut.setter
    @save
    def sent_shortcut(self, value):
        self._sent_shortcut = value

    @property
    def unread_shortcut(self):
        return self._unread_shortcut

    @unread_shortcut.setter
    @save
    def unread_shortcut(self, value):
        self._unread_shortcut = value

    @property
    def important_shortcut(self):
        return self._important_shortcut

    @important_shortcut.setter
    @save
    def important_shortcut(self, value):
        self._important_shortcut = value

    @property
    def starred_shortcut(self):
        return self._starred_shortcut

    @starred_shortcut.setter
    @save
    def starred_shortcut(self, value):
        self._starred_shortcut = value

    @property
    def trash_shortcut(self):
        return self._trash_shortcut

    @trash_shortcut.setter
    @save
    def trash_shortcut(self, value):
        self._trash_shortcut = value

    @property
    def spam_shortcut(self):
        return self._spam_shortcut

    @spam_shortcut.setter
    @save
    def spam_shortcut(self, value):
        self._spam_shortcut = value

    @property
    def send_email_shortcut(self):
        return self._send_email_shortcut

    @send_email_shortcut.setter
    @save
    def send_email_shortcut(self, value):
        self._send_email_shortcut = value

    @property
    def contacts_shortcut(self):
        return self._contacts_shortcut

    @contacts_shortcut.setter
    @save
    def contacts_shortcut(self, value):
        self._contacts_shortcut = value

    @property
    def settings_shortcut(self):
        return self._settings_shortcut

    @settings_shortcut.setter
    @save
    def settings_shortcut(self, value):
        self._settings_shortcut = value

    @property
    def resolution(self):
        return self._resolution

    @resolution.setter
    @save
    def resolution(self, value):
        self._resolution = value


options = OptionModel()
