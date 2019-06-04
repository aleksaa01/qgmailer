from googleapis.gmail.connection import GConnection
from googleapis.gmail.resources import ResourcePool
from googleapis.gmail.send import EmailSender


class SendEmailViewModel(object):

    def __init__(self):
        # At this point ResourcePool is already initialized
        # pass None as Resource is already initialized this point
        self.resource_pool = ResourcePool(GConnection())
        self.email_sender = None

    def run(self):
        self.email_sender = EmailSender(self.resource_pool.get())

    def send_email(self, to, subject, text):
        try:
            self.email_sender.send_email(to, subject, text)
            return True
        except:
            return False