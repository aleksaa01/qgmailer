from googleapis.gmail.connection import GConnection
from googleapis.people.connection import PConnection

from services.event_handlers import EventHandler
from services.calls import validate_http

import asyncio
import pickle
import time
from logs.loggers import default_logger


LOG = default_logger()

MAX_READ_BUF = 8192


def entrypoint(port):
    # TODO: Put a signal handler around this thing.
    #   For graceful shutdowns refer to this post: https://www.roguelynn.com/words/asyncio-graceful-shutdowns/
    asyncio.run(async_main(port))


async def parse(reader, writer):
    LOG.info("In parse coroutine.")
    raw_data = await reader.read(1)
    if len(raw_data) == 0:
        LOG.info("Unable to read, connection has been closed...")
        writer.close()
        await writer.wait_closed()
    request_len_size = ord(raw_data.decode('utf-8'))
    LOG.info("\trequest_len_size parsed...")

    raw_data = b''
    while len(raw_data) < request_len_size:
        chunk = await reader.read(request_len_size - len(raw_data))
        if len(chunk) == 0:
            LOG.info("Unable to read, connection has been closed...")
            writer.close()
            await writer.wait_closed()
        raw_data += chunk
    request_len = int(raw_data.decode('utf-8'))
    LOG.info("\trequest_len parsed...")

    raw_data = []
    received_data = 0
    while received_data < request_len:
        chunk = await reader.read(min(MAX_READ_BUF, request_len - received_data))
        received_data += len(chunk)
        raw_data.append(chunk)

    LOG.info("\trequest parsed...")

    api_event = pickle.loads(b''.join(raw_data))
    LOG.info("Returning from parse coroutine.")
    return api_event


async def write(data, writer):
    t = time.perf_counter()

    response_data = pickle.dumps(data)
    response_data_size = str(len(response_data))
    size_len = chr(len(response_data_size))
    raw_data = size_len.encode('utf-8') + response_data_size.encode('utf-8') + response_data

    LOG.info(f"Sending response back(response_data: {len(response_data)}, "
                f"response_data_size: {response_data_size}, size_len: {size_len}, len(raw_data): {len(raw_data)})...")
    writer.write(raw_data)
    await writer.drain()
    tt = time.perf_counter()
    LOG.info(f"Response sent in {tt - t} seconds !")


async def async_main(port):
    reader, writer = await asyncio.open_connection('localhost', port)
    LOG.info("Creating Gmail connection...")
    gmail_conn = GConnection()
    LOG.info("Creating People connection...")
    people_conn = PConnection()
    LOG.info("Acuiring resources...")
    gconn_list = [gmail_conn.acquire() for _ in range(6)]
    pconn_list = [people_conn.acquire()]
    LOG.info("Resources acquired...")

    # Populate cache with Gmail-API credentials.
    pft1 = time.perf_counter()
    ignore = gconn_list[0].users().messages().list(userId='me')
    await validate_http(ignore, {}, 'gmail')
    pft2 = time.perf_counter()
    LOG.info(f"Prefetching of credentials took: {pft2 - pft1} seconds.")

    read_task = None
    event_handler = EventHandler(gmail_conn, people_conn, gconn_list, pconn_list)
    while True:
        if read_task is None:
            LOG.info("Created new task for parsing input data.")
            read_task = asyncio.create_task(parse(reader, writer))
        elif read_task.done():
            api_event = read_task.result()
            await event_handler.handle_event(api_event)
            if event_handler.shutdown is True:
                writer.close()
                await writer.wait_closed()
                return
            read_task = None

        for api_event in event_handler.completed_tasks():
            LOG.info(f"Sending APIEvent(id: {api_event.event_id})....")
            await write(api_event, writer)

        await asyncio.sleep(0.000001)
