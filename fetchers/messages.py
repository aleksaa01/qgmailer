from PyQt5.QtCore import pyqtSignal, QThread
from googleapis.gmail.email_objects import MinimalMessage
from googleapis.gmail.requests import MessageRequest, MessageListRequest, BatchRequest
from googleapis.gmail.resources import ResourcePool

from multiprocessing import Process
from threading import Thread, current_thread
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
from googleapis.gmail.connection import GConnection
from googleapis.people.connection import PConnection

import time
from utils import APIEvent

CATEGORY_TO_QUERY = {
    'personal': 'in:personal',
    'social': 'in:social',
    'promotions': 'in:promotions',
    'updates': 'in:updates',
    'sent': 'in:sent',
    'trash': 'in:trash',
}

def fetch_message_list(resource, q, query, pages=2, page_len=100, page_token=None):
    def _batch_request_callback(request_id, response, exception=None):
        if exception:
            print("Error occured when fetching messages: {}".format(exception))
        idx = ord(request_id)
        msgs_page[idx] = MinimalMessage(response)

    # msglist_kwargs = {'userId': 'me', 'maxResults': self.page_len, 'q': self.query, 'pageToken': self.pt}
    # msglist_request = MessageListRequest(self.res_messages, self.release_callback)
    # msglist_request.set_kwargs(msglist_kwargs)
    page_token = page_token
    msglist_request = resource.users().messages().list(userId='me', maxResults=page_len, pageToken=page_token)
    headers = ['From', 'Subject']
    while pages > 0:
        msgs_resource = msglist_request.execute()

        # self.pt = msgs.get('nextPageToken', '')
        page_token = msgs_resource.get('nextPageToken', '')
        msgs_ids = msgs_resource.get('messages', [])
        msgs_page = [None] * len(msgs_ids)

        batch = resource.new_batch_http_request(_batch_request_callback)
        # msg_kwargs = {'userId': 'me', 'format': 'metadata', 'metadataHeaders': headers}
        # msg_request = MessageRequest(self.res_messages, self.release_callback, **msg_kwargs)
        for count, m in enumerate(msgs_ids):
            msg_request = resource.users().messages().get(id=m['id'], userId='me', format='metadata', metadataHeaders=headers)
            # Add request_id, which would be current index in messages_page in string.
            # Also pass None for callback, because I feel like Python just slows things
            # down when you pass him out of order kwargs, instead of full args.
            batch.add(msg_request, None, chr(count))
        # Looks like adding http object can help with performance (resource.http maybe ?)
        batch.execute()

        print('Page fetched... Query: {}'.format(query))
        q.put((resource, msgs_page))
        pages -= 1


class APIFetcher(Process):

    def __init__(self, input_queue, output_queue, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.input_queue = input_queue
        self.output_queue = output_queue

    def run(self):
        print('In run')
        t1 = time.perf_counter()
        self.gmail_conn = GConnection()
        self.people_conn = PConnection()
        self.gmail_resource_pool = ResourcePool(self.gmail_conn)
        self.gmail_resource_pool.create(5)
        self.people_res_pool = ResourcePool(self.people_conn)
        self.people_res_pool.create(1)
        self._worker_queue = Queue()
        self.event_map = {}
        t2 = time.perf_counter()
        print('API setup time:', t2 - t1)
        while True:
            if not self.input_queue.empty():
                print("Have something in the input queue...")
                api_event = self.input_queue.get(block=False)
                if api_event.type == 'gmail':

                    print("Total time before reading the first API Event:", time.time() - api_event.value)

                    gresource = self.gmail_resource_pool.get()
                    query = CATEGORY_TO_QUERY.get(api_event.category)
                    t = Thread(target=fetch_message_list,
                               args=(gresource, self._worker_queue, query))
                    self.event_map[gresource] = api_event
                    t.start()
                if api_event.type == None:
                    break
            elif not self._worker_queue.empty():
                print("Have something in the worker queue...")
                resource, data = self._worker_queue.get(block=False)
                api_event = self.event_map[resource]
                self.output_queue.put((api_event.event_id, data))
            else:
                time.sleep(0.1)

        return

class MessagesFetcher(Thread):

    pageLoaded = pyqtSignal(list)
    threadFinished = pyqtSignal(str)  # emits page token

    def __init__(self, resource1, resource2, release_callback, query, max_pages=0,
                 headers=None, msg_format='metadata', page_length=100, page_token=''):
        super().__init__(None)
        self.res_messages = resource1
        self.res_batch = resource2
        self.release_callback = release_callback
        self.query = query
        self.max_pages = max_pages if max_pages > 0 else 1000
        self.msg_format = msg_format
        self.headers = headers if headers else ['From', 'Subject']
        self.page_len = page_length
        self.pt = page_token

        self.msgs_page = []
        self.msg_count = 0

    def run(self):
        print('Running MessagesFetcher...')
        t1 = time.perf_counter()
        self.session_pages = self.max_pages
        self._load()
        self.threadFinished.emit(self.pt)
        t2 = time.perf_counter()
        print('Fetched messages in {} seconds.'.format(t2 - t1))

    def _load(self):
        session_pages = self.max_pages

        msglist_kwargs = {'userId': 'me', 'maxResults': self.page_len, 'q': self.query, 'pageToken': self.pt}
        msglist_request = MessageListRequest(self.res_messages, self.release_callback)
        msglist_request.set_kwargs(msglist_kwargs)
        while session_pages > 0:
            msgs = msglist_request.execute()

            self.pt = msgs.get('nextPageToken', '')
            messages_page = msgs.get('messages', [])
            self.msgs_page = [None] * len(messages_page)
            self.msg_count = 0

            batch = BatchRequest(self.res_batch, self._handle_batch_request)
            msg_kwargs = {'userId': 'me', 'format': self.msg_format, 'metadataHeaders': self.headers}
            msg_request = MessageRequest(self.res_messages, self.release_callback, **msg_kwargs)
            for m in messages_page:
                msg_request.update_kwargs('id', m['id'])
                batch.add(msg_request.build_request())
            batch.execute()

            self.pageLoaded.emit(self.msgs_page)

            msglist_request.update_kwargs('pageToken', self.pt)
            session_pages -= 1
            if not self.pt:
                break

    def _handle_batch_request(self, request_id, response, exception=None):
        if not response:
            return
        self.msgs_page[self.msg_count] = MinimalMessage(response)
        self.msg_count += 1


class MessageContentFetcher(QThread):

    fetched = pyqtSignal(str)

    def __init__(self, message_id=None, resource=None, release_callback=None, msg_format='raw', parent=None):
        super().__init__(parent)

        self.message_id = message_id
        self.res = resource
        self.msg_format = msg_format
        self.callback = release_callback

    def set_resource(self, resource, release_callback):
        self.res = resource
        self.callback = release_callback

    def set_message_id(self, new_message_id):
        self.message_id = new_message_id

    def run(self):
        kwargs = {'id': self.message_id, 'userId': 'me', 'format': self.msg_format}
        request = MessageRequest(self.res, self.callback, **kwargs)
        msg_content = request.execute()
        self.fetched.emit(msg_content['raw'])
        request.release()



import asyncio
import socket
import logging
import time
import pickle
import multiprocessing


MAX_READ_BUF = 8192


def entrypoint(port):
    asyncio.run(async_main(port))


async def parse(reader, writer):
    logger = multiprocessing.get_logger()
    logger.info("In parse coroutine.")
    raw_data = await reader.read(1)
    if len(raw_data) == 0:
        logger.info("Unable to read, connection has been closed...")
        writer.close()
        await writer.wait_closed()
    request_len_size = ord(raw_data.decode('utf-8'))

    raw_data = b''
    while len(raw_data) < request_len_size:
        chunk = await reader.read(request_len_size - len(raw_data))
        if len(chunk) == 0:
            logger.info("Unable to read, connection has been closed...")
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
    logger.info("Returning from parse coroutine.")
    return api_event


async def write(data, writer):
    logger = multiprocessing.get_logger()

    response_data = pickle.dumps(data)
    response_data_size = str(len(response_data))
    size_len = chr(len(response_data_size))
    raw_data = size_len.encode('utf-8') + response_data_size.encode('utf-8') + response_data

    logger.info("Sending response back...")
    writer.write(raw_data)
    await writer.drain()
    logger.info("Response sent!")



async def refresh_token(credentials):
    logger = multiprocessing.get_logger()

    body = {
        'grant_type': 'refresh_token',
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'refresh_token': credentials.refresh_token,
    }
    if credentials.scopes:
        body['scopes'] = ' '.join(credentials.scopes)

    post_data = urllib.parse.urlencode(body).encode('utf-8')
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    url = credentials.token_uri
    method = 'POST'

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=post_data, headers=headers) as response:
            if response.status == 200:
                response_data = json.loads(await response.text())
                credentials.token = response_data['access_token']
                credentials._refresh_token = response_data.get('refresh_token', credentials._refresh_token)
                credentials.expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=response_data.get('expires_in'))
                credentials._id_token = response_data.get('id_token')
            else:
                raise Exception(f"Failed in async refresh_token. Response status: {response.status}")


async def validate_http(http, headers):
    creds = http.http.credentials
    # check if creds are valid, and call refresh_token if they are not
    if creds.token is None or not creds.expired:
        await refresh_token(creds)
        headers['authorization'] = 'Bearer {}'.format(creds.token)
    return

