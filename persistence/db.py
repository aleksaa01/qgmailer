from settings import BASE_DIR

import sqlite3
import os

DB_PATH = os.path.join(BASE_DIR, 'data', 'data.db')


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
    # TODO: Consider maybe adding another text field to Message table,
    #  which would be a comma separated list of all the Label-IDs
    #  associated with that email message. This field would then have
    #  to be deserialized -> updated -> serialized -> saved.
    cur.execute('''
    CREATE TABLE Message(
    pk INTEGER PRIMARY KEY,
    message_id VARCHAR(16) NOT NULL,
    thread_id VARCHAR(16) NOT NULL,
    history_id VARCHAR(32) NOT NULL,
    field_to VARCHAR(256) NOT NULL,
    field_from VARCHAR(256) NOT NULL,
    subject VARCHAR(256) DEFAULT "",
    snippet VARCHAR(256) DEFAULT "",
    internal_date BIGINT NOT NULL
    );''')
    # Create table for keeping track of all Label IDs.
    # Individual label IDs should be represented by separate tables.
    # TODO: Because we have messages_total column in here, it implicates
    #  that we have to update it on every create/delete operation.
    #  But we can only update it before the database updates. It might get
    #  out of sync for short period of time, but that's fine.
    cur.execute('''
    CREATE TABLE LabelId (
    label_id VARCHAR(256) NOT NULL,
    label_name VARCHAR(256) NOT NULL,
    label_type VARCHAR(6) NOT NULL,
    message_list_visibility VARCHAR(4) NOT NULL,
    label_list_visibility VARCHAR(20) NOT NULL,
    messages_total INTEGER,
    text_color VARCHAR(7),
    background_color VARCHAR(7)
    );''')

    cur.execute('''
    CREATE TABLE Email(
    message_pk INTEGER,
    payload TEXT,
    CONSTRAINT fk_message
        FOREIGN KEY (message_pk)
        REFERENCES Message(pk)
        ON DELETE CASCADE
    );''')
    cur.execute('CREATE UNIQUE INDEX emailindex ON Email(message_pk);')

    return dbcon


def create_label_table(cursor, label_id):
    cursor.execute(f'''
    CREATE TABLE {label_id}(
    pk INTEGER PRIMARY KEY,
    message_pk INTEGER,
    CONSTRAINT fk_message
        FOREIGN KEY (message_pk)
        REFERENCES Message(pk)
        ON DELETE CASCADE
    );''')

    cursor.execute(f'CREATE UNIQUE INDEX {label_id}index ON {label_id}(message_pk);')
