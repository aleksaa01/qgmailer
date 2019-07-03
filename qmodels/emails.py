import sqlite3


DB_NAME = 'db_storage.db' # or load it like from settings



class EmailsModelBase(object):
    """
    There should exist only one database and it's name should be specified like in
    settings or somewhere.
    """

    table_name = ''
    table_fields = []

    def __init__(self):
        self.con = sqlite3.connect(DB_NAME)
        self.cursor = self.con.cursor()

        # for the start you don't need some advance logic for this
        # having pre defined queries is enough.
        self.load_query = 'SELECT * FROM {}'.format(self.table_name)
        self.update_query = 'INSERT INTO ' + self.table_name + ' VALUES(' + '?,' * (len(self.table_fields) - 1) + '?)'
        self.delete_query = 'DELETE FROM {} WHERE '.format(self.table_name)

    def load(self, query=None):
        query = query if query else self.load_query
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def update(self, data, query=None):
        query = query if query else self.update_query
        self.cursor.executemany(query, data)
        self.con.commit()

    def delete(self, name, value, query=None):
        """
        :param name: Table column name.
        :param value: Table column value
        :param query: Pass your custom query to this parameter.
        """
        query = query if query else self.delete_query
        query += '{}={}'.format(name, value)

        self.cursor.execute(query)
        self.con.commit()

    def terminate(self):
        self.cusor.close()
        self.con.close()


class PersonalEmailsModel(EmailsModelBase):
    table_name = 'PersonalEmails'
    table_fields = ['id', 'snippet', 'historyId', 'who', 'subject']

    """
    BIG QUESTION: Should I make model dumb, so it just retuns raw data and let ViewModels interpret it however they want
    Or should I convert raw data to some custom objects that are easier to work with and then return them ???
    I am leaning more toward NOT making my Model have that additional logic.
    EDIT: Yes, you shouldn't make your model more complex by introducing custom objects.
    """

    def __init__(self):
        super().__init__()


class SocialEmailsModel(EmailsModelBase):
    def __init__(self):
        super().__init__()


class PromotionsEmailsModel(EmailsModelBase):
    def __init__(self):
        super().__init__()


class UpdatesEmailsModel(EmailsModelBase):
    def __init__(self):
        super().__init__()


class SentEmailsModel(EmailsModelBase):
    def __init__(self):
        super().__init__()


class TrashEmailsModel(EmailsModelBase):
    def __init__(self):
        super().__init__()