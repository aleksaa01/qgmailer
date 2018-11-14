from email.mime.text import MIMEText
from base64 import urlsafe_b64decode, urlsafe_b64encode


class EmailSender(object):

    def __init__(self, resource, user_email=None):
        self.res = resource
        self.user_email = user_email

    def send_email(self, to, subject, text):
        self.send(self.create_message(to, subject, text))

    def send(self, mime_message):
        try:
            returned_message = self.res.users().messages().send(
                userId='me', body=mime_message).execute()
        except Exception as err:
            raise Exception("Failed to send the message: {}".format(str(err)))
        else:
            print('Message sent successfully!')

    def create_message(self, to, subject, text):
        message = MIMEText(text)
        message['to'] = to
        message['subject'] = subject

        if self.user_email is None:
            self._fetch_user_email()
        message['sender'] = self.user_email

        base64_message = urlsafe_b64encode(message.as_bytes())
        mime_message = base64_message.decode()

        return {'raw': mime_message}

    def _fetch_user_email(self):
        profile = self.res.users().getProfile(userId='me').execute()
        self.user_email = profile['emailAddress']
