class ContactObject(object):

    def __init__(self, contact_dict):
        self.resource_name = contact_dict['resourceName']
        self.etag = contact_dict['etag']

        names = contact_dict.get('names', [])
        emails = contact_dict.get('emailAddresses', [])

        self.name = ''
        self.email = ''
        if names:
            self.name = names[0]['displayName']
        if emails:
            self.email = emails[0]['value']

    def edit_contact(self, resource):
        raise NotImplemented('edit_contact is not implemented yet.')

    def remove_contact(self, resource):
        raise NotImplemented('remove_contact is not implemented yet.')

