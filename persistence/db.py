from settings import BASE_DIR
from logs.loggers import default_logger

import sqlite3
import os
import time

LOG = default_logger()

DB_PATH = os.path.join(BASE_DIR, 'data', 'data.db')
app_info_cache = None


def check_if_db_exists():
    return os.path.exists(DB_PATH)


def db_connect(path=DB_PATH):
    dbcon = sqlite3.connect(path)
    # Enable foreign key support by default
    enable_foreign_keys(dbcon.cursor())
    return dbcon


def enable_foreign_keys(cursor):
    # You have to run this pragma in order to enable foreign key support.
    cursor.execute('PRAGMA foreign_keys = 1;')


def db_setup():
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.mkdir(os.path.dirname(DB_PATH))

    with open(DB_PATH, 'wb') as f:
        pass

    dbcon = db_connect()
    cur = dbcon.cursor()

    # Create table for email messages.
    # Note that SQLite doesn't care about restricted length of columns.
    # And will allow all of them to have any number of characters.
    # Message ids can't be longer than 16 characters(at least up until year 2527).
    # I don't know maximum length of the history-id yet.
    # Maximum email length(Email Path) is 256 characters. For example me@example.com:
    # Local-part(me) + @ + Domain(example.com) = Full Path(me@example.com)
    # UPDATE: Looks like message id, thread it and history id can actually be represented
    # as integers because of certain characteristics, although I have to do some
    # conversion before persisting them.
    cur.execute('''
    CREATE TABLE Message(
    message_id BIGINT PRIMARY KEY NOT NULL,
    thread_id BIGINT NOT NULL,
    history_id INTEGER NOT NULL,
    field_to VARCHAR(256) NOT NULL,
    field_from VARCHAR(256) NOT NULL,
    subject VARCHAR(256) DEFAULT "",
    snippet VARCHAR(256) DEFAULT "",
    internal_date BIGINT NOT NULL,
    label_ids TEXT NOT NULL
    );''')
    cur.execute('CREATE INDEX messageindex ON Message(internal_date);')
    # Create table for keeping track of all Label IDs.
    # Individual label IDs should be represented by separate tables.
    # Message/label list visibility can be None, for example UNREAD label
    # has neither of those.
    cur.execute('''
    CREATE TABLE Label (
    label_id VARCHAR(256) NOT NULL,
    label_name VARCHAR(256) NOT NULL,
    label_type VARCHAR(6) NOT NULL,
    message_list_visibility VARCHAR(4),
    label_list_visibility VARCHAR(20),
    messages_total INTEGER,
    text_color VARCHAR(7),
    background_color VARCHAR(7)
    );''')

    cur.execute('''
    CREATE TABLE Email(
    message_pk BIGINT,
    payload TEXT,
    CONSTRAINT fk_message
        FOREIGN KEY (message_pk)
        REFERENCES Message(message_id)
        ON DELETE CASCADE
    );''')
    cur.execute('CREATE UNIQUE INDEX emailindex ON Email(message_pk);')

    cur.execute('''
    CREATE TABLE AppInfo(
    last_synced_date BIGINT,
    date_of_oldest_email BIGINT,
    last_time_synced REAL
    );''')
    cur.execute('''INSERT INTO AppInfo VALUES(null, null, null);''')
    dbcon.commit()

    return dbcon


class AppInfoCache:
    def __init__(self, last_synced_date=None, date_of_oldest_email=None, last_time_synced=None):
        # date of the last synced email. This is used for tracking PSSQP progress.
        # Should be in internal_date format.
        self.last_synced_date = last_synced_date
        # Oldest email in user's inbox. Should be in internal_date format.
        self.date_of_oldest_email = date_of_oldest_email
        # Last time we synced(full or short). Should be in start_of_sync.timestamp() format.
        self.last_time_synced = last_time_synced

    def update(self, db):
        # Check if fields are of right type, ignore None values.
        if (self.last_synced_date and not isinstance(self.last_synced_date, int)) \
        or (self.date_of_oldest_email and not isinstance(self.date_of_oldest_email, int)) \
        or (self.last_time_synced and not isinstance(self.last_time_synced, float)):
            raise TypeError(
                "Can't update AppInfo table, fields are of wrong type."
                f"Expected (int, int, float), got ({type(self.last_synced_date)}, "
                f"{type(self.date_of_oldest_email)}, {type(self.last_time_synced)})."
            )

        db.execute(
            'update AppInfo set last_synced_date=?, date_of_oldest_email=?, last_time_synced=?;',
            (self.last_synced_date, self.date_of_oldest_email, self.last_time_synced)
        )
        t1 = time.perf_counter()
        db.commit()
        t2 = time.perf_counter()
        LOG.warning(f"Commit in AppInfo.update took {t2 - t1} seconds to execute.")

    @classmethod
    def load(cls, db):
        a, b, c = db.execute('select * from AppInfo;').fetchone()
        return cls(a, b, c)


def get_app_info(db):
    global app_info_cache
    if app_info_cache is None:
        app_info_cache = AppInfoCache.load(db)

    return app_info_cache
