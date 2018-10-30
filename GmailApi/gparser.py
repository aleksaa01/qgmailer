from mailparser.mailparser import MailParser
from base64 import urlsafe_b64decode


class NoBoundaryMailParser(MailParser):

    @property
    def body(self):
        return self.text_plain, self.text_html


def extract_body(raw_message):
    """

    :param raw_message: dictionary that you got from
            resource.users().messages().get() in raw format.
    :return: email_body(string), list_of_attachments(list of dictionaries)
    """

    # urlsafe_b64decode returns bytes, so you need to decode it.
    # And sometimes when decoding you can encounter weird characters,
    # so add argument errors='replace'
    email = urlsafe_b64decode(raw_message['raw']).decode('utf-8', errors='replace')

    mail_parser = NoBoundaryMailParser.from_string(email)

    try:
        # mailparser docs: https://github.com/SpamScope/mail-parser/
        plain, html = mail_parser.body
        if html:
            print('::return html part::')
            return "\n".join(html), mail_parser.attachments
        else:
            print('::return plain part::')
            return "\n".join(plain), mail_parser.attachments
    except Exception as err:
        print('Extracting body with "mailparser" failed.', str(err))
        return mail_parser
