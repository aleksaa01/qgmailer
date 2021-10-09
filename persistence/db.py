from settings import BASE_DIR
from logs.loggers import default_logger
import os
import time
import aiosqlite

LOG = default_logger()

DB_PATH = os.path.join(BASE_DIR, 'data', 'data.db')
DB_SYNC_COPY_DEFAULT_NAME = 'data_copy.db'
DB_SYNC_COPY_PATH = os.path.join(BASE_DIR, 'data', 'data_copy.db')
app_info_cache = None
CONNECTION_POOL = []
CONNECTION_POOL_MAXSIZE = 4


async def spin_up_connections(alive_connections=None):
    if alive_connections and isinstance(alive_connections, (list, tuple)):
        for idx in range(min(len(alive_connections), CONNECTION_POOL_MAXSIZE)):
            CONNECTION_POOL.append(alive_connections[idx])

    for _ in range(CONNECTION_POOL_MAXSIZE - len(CONNECTION_POOL)):
        CONNECTION_POOL.append(await db_connect())


async def close_all_connections():
    for con in CONNECTION_POOL:
        await con.close()


async def acquire_connection():
    if len(CONNECTION_POOL) > 0:
        return CONNECTION_POOL.pop()
    else:
        return await db_connect()


async def release_connection(con):
    if len(CONNECTION_POOL) <= CONNECTION_POOL_MAXSIZE:
        CONNECTION_POOL.append(con)
    else:
        await con.close()


async def force_full_checkpoint():
    # PASSIVE checkpoint is recommended if db is actively accessed.
    # FULL is only for one-offs, like making sure db is fully up to date before copying it.
    con = await db_connect()
    await con.execute('PRAGMA wal_checkpoint(FULL);')
    await con.close()


async def make_db_copy():
    with open(DB_PATH, 'rb') as read_fh:
        with open(DB_SYNC_COPY_PATH, 'wb') as write_fh:
            write_fh.write(read_fh.read())


def check_if_db_exists():
    return os.path.exists(DB_PATH)


def check_if_db_copy_exists():
    return os.path.exists(DB_SYNC_COPY_PATH)


async def db_connect(path=DB_PATH):
    dbcon = await aiosqlite.connect(path)
    await _run_nonpersistent_pragmas(dbcon)
    return dbcon


async def _run_persistent_pragmas(conn):
    # Switch from 'journal' mode to 'wal' mode for concurrent reads and writes(Write Ahead Logging).
    await conn.execute('PRAGMA journal_mode = WAL;')


async def _run_nonpersistent_pragmas(conn):
    # Obtain exclusive lock in order to prevent other processes from accessing the db file.
    # await conn.execute('PRAGMA locking_mode = EXCLUSIVE;')
    # Enable foreign key support.
    await conn.execute('PRAGMA foreign_keys = ON;')


async def db_setup():
    if not check_if_db_exists():
        if not os.path.exists(os.path.dirname(DB_PATH)):
            os.mkdir(os.path.dirname(DB_PATH))
        dbcon = await aiosqlite.connect(DB_PATH)
        await _run_persistent_pragmas(dbcon)
        await _run_nonpersistent_pragmas(dbcon)
    else:
        dbcon = await db_connect()

    cur = await dbcon.cursor()

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
    # TODO: Maybe add index on internal_date column.
    await cur.execute('''
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
    await cur.execute('CREATE INDEX messageindex ON Message(internal_date);')
    # Create table for keeping track of all Label IDs.
    # Individual label IDs should be represented by separate tables.
    # Message/label list visibility can be None, for example UNREAD label
    # has neither of those.
    await cur.execute('''
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

    await cur.execute('''
    CREATE TABLE Email(
    message_pk BIGINT,
    payload TEXT,
    CONSTRAINT fk_message
        FOREIGN KEY (message_pk)
        REFERENCES Message(message_id)
        ON DELETE CASCADE
    );''')
    await cur.execute('CREATE UNIQUE INDEX emailindex ON Email(message_pk);')

    await cur.execute('''
    CREATE TABLE Contact(
    resource_name VARCHAR(256) PRIMARY KEY NOT NULL,
    etag VARCHAR(256),
    name VARCHAR(256),
    email VARCHAR(256)
    );''')

    await cur.execute('''
    CREATE TABLE AppInfo(
    last_synced_date BIGINT,
    date_of_oldest_email BIGINT,
    last_time_synced REAL,
    latest_history_id BIGINT
    );''')
    await cur.execute('''INSERT INTO AppInfo VALUES(null, null, null, null);''')
    await dbcon.commit()

    return dbcon


async def create_change_list_table():
    db = await db_connect()
    await db.execute('''
    CREATE TABLE IF NOT EXISTS ChangeList(
    id INTEGER PRIMARY KEY NOT NULL,
    api_type VARCHAR(255),
    action_type VARCHAR(255),
    payload TEXT  /* serialized JSON version of the data record. */
    );''')


class AppInfoCache:
    def __init__(self, last_synced_date=None, date_of_oldest_email=None, last_time_synced=None,
                 latest_history_id=None):
        # date of the last synced email. This is used for tracking PSSQP progress.
        # Should be in internal_date format.
        self.last_synced_date = last_synced_date
        # Oldest email in user's inbox. Should be in internal_date format.
        self.date_of_oldest_email = date_of_oldest_email
        # Last time we synced(full or short). Should be in start_of_sync.timestamp() format.
        self.last_time_synced = last_time_synced
        # Latest history id, history ids seem to always go up, and duplicates are possible.
        self.latest_history_id = latest_history_id

    async def update(self):
        db = await acquire_connection()

        # Check if fields are of right type, ignore None values.
        if (self.last_synced_date and not isinstance(self.last_synced_date, int)) \
        or (self.date_of_oldest_email and not isinstance(self.date_of_oldest_email, int)) \
        or (self.last_time_synced and not isinstance(self.last_time_synced, float)) \
        or (self.latest_history_id and not isinstance(self.latest_history_id, int)):
            raise TypeError(
                "Can't update AppInfo table, fields are of wrong type."
                f"Expected (int, int, float, int), got ({type(self.last_synced_date)}, "
                f"{type(self.date_of_oldest_email)}, {type(self.last_time_synced)}), "
                f"{type(self.latest_history_id)}."
            )

        await db.execute(
            'UPDATE AppInfo SET last_synced_date=?, date_of_oldest_email=?, last_time_synced=?, '
            'latest_history_id=?;',
            (self.last_synced_date, self.date_of_oldest_email, self.last_time_synced,
             self.latest_history_id)
        )
        t1 = time.perf_counter()
        await db.commit()
        await release_connection(db)
        t2 = time.perf_counter()
        LOG.warning(f"Commit in AppInfo.update took {t2 - t1} seconds to execute.")

    @classmethod
    async def load(cls):
        db = await acquire_connection()
        data = await db.execute_fetchall('SELECT * FROM AppInfo;')
        a, b, c, d = data[0]
        await release_connection(db)
        return cls(a, b, c, d)


async def get_app_info():
    global app_info_cache
    if app_info_cache is None:
        app_info_cache = await AppInfoCache.load()

    return app_info_cache
