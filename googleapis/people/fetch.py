from googleapis._fetch import BaseFetcher
from googleapis.people.contact_objects import ContactObject
from options import Options

from PySide2.QtCore import Signal


PERSON_FIELDS = (
    'addresses', 'ageRanges', 'biographies', 'birthdays',
    'braggingRights', 'coverPhotos', 'emailAddresses', 'events',
    'genders', 'imClients', 'interests', 'locales', 'memberships',
    'metadata', 'names', 'nicknames', 'occupations', 'organizations',
    'phoneNumbers', 'photos', 'relations', 'relationshipInterests',
    'relationshipStatuses', 'residences', 'sipAddresses', 'skills',
    'taglines', 'urls', 'userDefined'
)


class ContactsFetcher(BaseFetcher):

    pageLoaded = Signal(list)
    PAGE_LENGTH = Options.app_options['contacts_per_page']

    def __init__(self, resource, fields=None, filename='', parent=None):
        super().__init__(resource, filename, parent)

        self.contacts = []

        if fields:
            for field in fields:
                if field not in PERSON_FIELDS:
                    raise ValueError('Field {} doesn\'t exist.'.format(field))
            self.fields = ','.join(fields)
        else:
            self.fields = 'names,emailAddresses'

        self.npt = ''
        self.num_pages = 0

    def run(self):
        print('Running thread...')
        if self.filename:
            self.load_from_file()
        else:
            self.npt = 'temp'
            self.load_from_api()

        self.threadFinished.emit(self.contacts)

    def load_from_file(self):
        super().load_from_file()

    def load_from_api(self):
        while self.npt:
            self.num_pages += 1

            if self.num_pages == 1:
                page = self.res.people().connections().list(
                    resourceName='people/me',
                    pageSize=self.PAGE_LENGTH,
                    personFields=self.fields).execute()
            else:
                page = self.res.people().connections().list(
                    resourceName='people/me',
                    pageSize=self.PAGE_LENGTH,
                    pageToken=self.npt,
                    personFields=self.fields).execute()

            for contact_dict in page.get('connections', []):
                self.contacts.append(ContactObject(contact_dict))
            self.npt = page.get('nextPageToken', '')

            if self.num_pages == 1:
                self.pageLoaded.emit(self.contacts[:])

