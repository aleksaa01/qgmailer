class ContactObject(object):

    """
    Create contact by calling createContact().
    Specify body. Body is dictionary of specified fields.

    Update contact by calling updateContact().
    Specify resourceName, body, updateFields. Body should have etag specified.
    """

    def __init__(self, contact_dict=None):
        self.name = ''
        self.email = ''

        if contact_dict is None:
            return

        self.resource_name = contact_dict['resourceName']
        self.etag = contact_dict['etag']

        names = contact_dict.get('names', [])
        emails = contact_dict.get('emailAddresses', [])

        if names:
            self.name = names[0]['displayName']
        if emails:
            self.email = emails[0]['value']

    def edit_contact(self, service):
        raise NotImplemented('edit_contact is not implemented yet.')

    def remove_contact(self, service):
        raise NotImplemented('remove_contact is not implemented yet.')

