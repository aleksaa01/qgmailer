from googleapis.gmail.connection import GmailConnection
from googleapis.people.connection import PeopleConnection

from persistence.db import spin_up_connections, check_if_db_exists, db_setup, close_all_connections, \
    force_full_checkpoint, make_db_copy, check_if_db_copy_exists, create_change_list_table, DB_PATH, \
    db_connect, DB_SYNC_COPY_PATH
from services.event_handlers import EventHandler, OfflineEventHandler, apply_offline_changes
from services.api_calls import validate_http
from services.calls import full_sync, short_sync
from logs.loggers import default_logger

from aiohttp.client_exceptions import ClientConnectionError

import asyncio
import pickle
import time
import os


LOG = default_logger()

MAX_READ_BUF = 8192


def entrypoint(port):
    # TODO: Put a signal handler around this thing.
    #   For graceful shutdowns refer to this post: https://www.roguelynn.com/words/asyncio-graceful-shutdowns/
    asyncio.run(async_main(port))
    LOG.info("AsyncIO loop no longer active.")


async def parse(reader, writer):
    raw_data = await reader.read(1)
    if len(raw_data) == 0:
        LOG.warning("Unable to read, connection has been closed...")
        writer.close()
        await writer.wait_closed()
    request_len_size = ord(raw_data.decode('utf-8'))

    raw_data = b''
    while len(raw_data) < request_len_size:
        chunk = await reader.read(request_len_size - len(raw_data))
        if len(chunk) == 0:
            LOG.warning("Unable to read, connection has been closed...")
            writer.close()
            await writer.wait_closed()
        raw_data += chunk
    request_len = int(raw_data.decode('utf-8'))

    raw_data = []
    received_data = 0
    while received_data < request_len:
        chunk = await reader.read(min(MAX_READ_BUF, request_len - received_data))
        received_data += len(chunk)
        raw_data.append(chunk)

    api_event = pickle.loads(b''.join(raw_data))
    return api_event


async def write(data, writer):
    t = time.perf_counter()

    response_data = pickle.dumps(data)
    response_data_size = str(len(response_data))
    size_len = chr(len(response_data_size))
    raw_data = size_len.encode('utf-8') + response_data_size.encode('utf-8') + response_data

    writer.write(raw_data)
    await writer.drain()
    tt = time.perf_counter()
    LOG.debug(f"Response sent in {tt - t} seconds !")


async def async_main(port):
    reader, writer = await asyncio.open_connection('localhost', port)

    # We don't check is user has an internet connection before running the flow because we can just
    # assume that user knows it has to authorize the application first.
    LOG.debug("Creating Gmail connection...")
    gmail_conn = GmailConnection()
    LOG.debug("Creating People connection...")
    people_conn = PeopleConnection()
    LOG.debug("Acuiring resources...")
    gconn_list = [gmail_conn.acquire() for _ in range(6)]
    pconn_list = [people_conn.acquire()]
    LOG.debug("Resources acquired...")

    in_offline_mode = False
    # Populate cache with Gmail-API credentials.
    ignore = gconn_list[0].users().messages().list(userId='me')
    try:
        await validate_http(ignore, {})
        if check_if_db_copy_exists():
            if not check_if_db_exists():
                # This is more like a failure prevention. data_copy.db exist but not data.db
                # So I have to delete everything from data directory and start from scratch(full sync)
                LOG.warning("data_copy.db exists, but data.db doesn't. "
                            "Wiping everything and starting full sync from the beginning...")
                dirname = os.path.dirname(DB_PATH)
                for file_name in os.listdir(dirname):
                    os.remove(os.path.join(dirname, file_name))
            else:
                # Apply all changes
                db = await db_connect()
                change_list = await db.execute_fetchall('SELECT * FROM ChangeList;')
                await apply_offline_changes(gconn_list[0], db, change_list)
                await db.close()
                await force_full_checkpoint()
                os.remove(DB_PATH)  # Remove old db
                os.rename(DB_SYNC_COPY_PATH, DB_PATH)
                # Run short sync
                await short_sync(gconn_list[0], max_results=50)
    except ClientConnectionError:
        # No Internet connection, switch to Offline Mode.
        in_offline_mode = True
        if check_if_db_copy_exists():
            # TODO: Load data from the ChangeList. Need once you add offline support for contacts.
            pass
        else:
            LOG.debug("Calling force_full_checkpoint...")
            await force_full_checkpoint()
            LOG.debug("Calling make_db_copy...")
            await make_db_copy()
            LOG.debug("Calling create_change_list_table...")
            await create_change_list_table()

    if check_if_db_exists():
        await spin_up_connections()
    else:
        con = await db_setup()
        await spin_up_connections((con,))

    if in_offline_mode is False:
        # This will start full sync in the 'background' if necessary.
        # FIXME: Run full sync if last sync was done more than a week ago, otherwise run short sync.
        full_sync_conn = gmail_conn.acquire()
        full_sync_task = asyncio.create_task(full_sync(full_sync_conn))

        event_handler = EventHandler(gmail_conn, people_conn, gconn_list, pconn_list)
    else:
        full_sync_task = None
        event_handler = OfflineEventHandler()

    read_task = None
    while True:
        if full_sync_task and full_sync_task.done():
            gconn_list.append(full_sync_conn)
            full_sync_task = None
        if read_task is None:
            read_task = asyncio.create_task(parse(reader, writer))
        elif read_task.done():
            api_event = read_task.result()
            await event_handler.handle_event(api_event)
            if event_handler.shutdown is True:
                # TODO: If I want to conduct graceful shutdowns, then this might be the right place to do it.
                #   but it's not the only one, because the outer loop should deal with kill signals.
                writer.close()
                await writer.wait_closed()
                await close_all_connections()
                return
            read_task = None

        for api_event in event_handler.completed_tasks():
            await write(api_event, writer)

        await asyncio.sleep(0.000001)
