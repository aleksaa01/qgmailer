from mailparser.mailparser import MailParser
from base64 import urlsafe_b64decode


class NoBoundaryMailParser(MailParser):

    @property
    def body(self):
        return self.text_plain, self.text_html


def extract_body(raw_message):
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
            return "\n".join(html)
        else:
            print('::return plain part::')
            return "\n".join(plain)
    except Exception as err:
        print('Extracting body with "mailparser" failed.', str(err))
        print(email)
        return mail_parser
