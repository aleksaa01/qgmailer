from googleapis.gmail.connection import GConnection
from googleapis.people.connection import PConnection

from utils import APIEvent, IPC_SHUTDOWN
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.feedparser import FeedParser
from email.generator import Generator
from urllib.parse import urlparse, urlunparse
from io import StringIO

import datetime
import json
import asyncio
import time
import pickle
import multiprocessing
import time
import aiohttp
import uuid
import urllib
import httplib2


CATEGORY_TO_QUERY = {
    'personal': 'in:personal',
    'social': 'in:social',
    'promotions': 'in:promotions',
    'updates': 'in:updates',
    'sent': 'in:sent',
    'trash': 'in:trash',
}


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


async def async_main(port):
    logger = multiprocessing.get_logger()
    logger.info("Logger obtained in child process.")
    reader, writer = await asyncio.open_connection('localhost', port)

    logger.info("Creating Gmail connection...")
    gmail_conn = GConnection()
    logger.info("Creating People connection...")
    people_conn = PConnection()
    logger.info("Acuiring resources...")
    gconn_list = [gmail_conn.acquire() for _ in range(6)]
    pconn_list = [people_conn.acquire()]

    # page token cache for ApiEvent.category
    token_cache = {}
    api_requests = {}
    ipc_read_task = None
    api_tasks = []
    while True:
        if ipc_read_task is None:
            logger.info("Created new task for parsing input data. <1>")
            ipc_read_task = asyncio.create_task(parse(reader, writer))
        elif ipc_read_task.done():
            api_event = ipc_read_task.result()
            if api_event.value == IPC_SHUTDOWN:
                logger.info("Received IPC_SHUTDOWN. Shutting down...")
                writer.close()
                await writer.wait_closed()
                break
            ipc_read_task = None

            query = CATEGORY_TO_QUERY.get(api_event.category)
            if len(gconn_list) == 0:
                gconn_list.append(gmail_conn.acquire())
            resource = gconn_list.pop()

            logger.info("Created task for fetch_messaegs. <2>")
            api_task = asyncio.create_task(fetch_messages(resource, query))
            api_tasks.append(api_task)
            api_requests[api_task] = (resource, api_event.event_id)

        for task in api_tasks[:]:
            if task.done():
                logger.info("Api task done.")
                resource, event_id = api_requests[task]
                gconn_list.append(resource)
                response_api_event = APIEvent(event_id, value=task.result())
                logger.info("Creating task for IPC write... <11>")
                asyncio.create_task(write(response_api_event, writer))
                api_tasks.remove(task)

        await asyncio.sleep(0.000001)


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

    logger.info("Getting access_token from Gmail API... <5>")
    t1, p1 = time.time(), time.perf_counter()
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=post_data, headers=headers) as response:
            if response.status == 200:
                response_data = json.loads(await response.text(encoding='utf-8'))
                credentials.token = response_data['access_token']
                credentials._refresh_token = response_data.get('refresh_token', credentials._refresh_token)
                credentials.expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=response_data.get('expires_in'))
                credentials._id_token = response_data.get('id_token')
            else:
                raise Exception(f"Failed in async refresh_token. Response status: {response.status}")
    t2, p2 = time.time(), time.perf_counter()
    logger.info(f"Time lapse for getting access_token from Gmail-API(t, p): {t2 - t1}, {p2 - p1}")


async def validate_http(http, headers):
    logger = multiprocessing.get_logger()

    creds = http.http.credentials
    # check if creds are valid, and call refresh_token if they are not
    if creds.token is None or not creds.expired:
        logger.info("Calling refresh_token... <4>")
        await asyncio.create_task(refresh_token(creds))
        headers['authorization'] = 'Bearer {}'.format(creds.token)
    return


async def fetch_messages(resource, query, headers=None, msg_format='metadata', max_results=100, page_token=''):

    logger = multiprocessing.get_logger()

    if headers is None:
        headers = ['From', 'Subject']

    http = resource.users().messages().list(userId='me', maxResults=max_results, q=query, pageToken=page_token)
    headers = http.headers
    if "content-length" not in headers:
        headers["content-length"] = str(http.body_size)

    try:
        logger.info("Calling validate_http... <3>")
        await asyncio.create_task(validate_http(http, headers))
        t1, p1 = time.time(), time.perf_counter()
        async with aiohttp.ClientSession() as session:
            async with session.get(http.uri, headers=headers) as response:
                if 200 <= response.status < 300:
                    response_data = json.loads(await response.text(encoding='utf-8'))
                else:
                    raise Exception("Failed to get data back. Response status: ", response.status)
        t2, p2 = time.time(), time.perf_counter()
        logger.info(f"Time lapse for fetching list of messages from Gmail-API(t, p): {t2 - t1}, {p2 - p1}")
    except Exception as err:
        logger.warning(f"Encountered an exception: {err}")
        raise Exception

    batch = BatchApiRequest()
    for msg in response_data.get('messages'):
        http_request = resource.users().messages().get(
            id=msg['id'], userId='me', format='metadata', metadataHeaders=['From', 'Subject']
        )
        batch.add(http_request)
    logger.info("Calling execute... <6>")
    t1, p1 = time.time(), time.perf_counter()
    responses = await asyncio.create_task(batch.execute(headers['authorization']))
    t2, p2 = time.time(), time.perf_counter()
    logger.info(f"Got responses back. t2 - t1, p2 - p1: {t2 - t1}, {p2 - p1}")
    logger.info(f"First response: {responses[0]}")

    return responses


class BatchError(Exception): pass


class BatchApiRequest(object):
    MAX_BATCH_LIMIT = 1000

    def __init__(self):
        self.requests = []
        self._batch_uri = 'https://gmail.googleapis.com/batch'
        self._base_id = uuid.uuid4()

    def add(self, http_request):
        if len(self.requests) >= self.MAX_BATCH_LIMIT:
            raise BatchError(
                f"Exceeded the maximum calls({self.MAX_BATCH_LIMIT}) in a single batch request."
            )
        self.requests.append(http_request)

    def _id_to_header(self, id_):
        return f"<{self._base_id} + {id_}>"

    async def _serialize_request(self, request):
        """
        Convert an HttpRequest object into a string.

        Args:
          request: HttpRequest, the request to serialize.

        Returns:
          The request as a string in application/http format.
        """
        parsed = urlparse(request.uri)
        request_line = urlunparse(
            ("", "", parsed.path, parsed.params, parsed.query, "")
        )
        status_line = request.method + " " + request_line + " HTTP/1.1\n"
        major, minor = request.headers.get("content-type", "application/json").split(
            "/"
        )
        msg = MIMENonMultipart(major, minor)
        headers = request.headers.copy()

        # MIMENonMultipart adds its own Content-Type header.
        if "content-type" in headers:
            del headers["content-type"]

        for key, value in headers.items():
            msg[key] = value
        msg["Host"] = parsed.netloc
        msg.set_unixfrom(None)

        if request.body is not None:
            msg.set_payload(request.body)
            msg["content-length"] = str(len(request.body))

        # Serialize the mime message.
        fp = StringIO()
        # maxheaderlen=0 means don't line wrap headers.
        g = Generator(fp, maxheaderlen=0)
        g.flatten(msg, unixfrom=False)
        body = fp.getvalue()

        return status_line + body

    async def execute(self, access_token):
        """Validated credentials before calling this coroutine."""
        logger = multiprocessing.get_logger()

        message = MIMEMultipart("mixed")
        # Message should not write out it's own headers.
        setattr(message, "_write_headers", lambda arg: None)

        logger.info("Looping through request...")

        for rid, request in enumerate(self.requests):
            msg_part = MIMENonMultipart("application", "http")
            msg_part["Content-Transfer-Encoding"] = "binary"
            msg_part["Content-ID"] = self._id_to_header(str(rid))

            if rid == 0:
                logger.info("Calling _serialize_request in for loop... <7>")

            body = await asyncio.create_task(self._serialize_request(request))
            msg_part.set_payload(body)
            message.attach(msg_part)

        logger.info("Flatening message...")
        fp = StringIO()
        g = Generator(fp, mangle_from_=False)
        g.flatten(message, unixfrom=False)
        body = fp.getvalue()

        headers = {}
        headers["content-type"] = f'multipart/mixed; boundary="{message.get_boundary()}"'
        headers['authorization'] = access_token

        logger.info("Sending request... <8>")
        t1, p1 = time.time(), time.perf_counter()
        async with aiohttp.ClientSession() as session:
            async with session.post(url=self._batch_uri, data=body, headers=headers) as response:
                if response.status < 200 or response.status >= 300:
                    raise Exception("Batch request failed. Response status: ", response.status)
                else:
                    content = await response.text(encoding='utf-8')
        t2, p2 = time.time(), time.perf_counter()
        logger.info(f"Time lapse for getting response from Batch request(t, p): {t2 - t1}, {p2 - p1}")
        logger.info("Calling parse_response... <9>")
        return await asyncio.create_task(self.parse_response(response, content))

    async def parse_response(self, response, content):
        logger = multiprocessing.get_logger()
        logger.info("Parsing response...")

        header = f"content-type: {response.headers['content-type']}\r\n\r\n"
        for_parser = header + content
        parser = FeedParser()
        parser.feed(for_parser)
        mime_response = parser.close()

        logger.info(f"mime_response.is_multipart(): {mime_response.is_multipart()}")

        responses = []
        # Separation of the multipart response message.
        count = 0 # DELETE
        for part in mime_response.get_payload():
            request_id = self._header_to_id(part["Content-ID"])

            count += 1
            if count == 0:
                logger.info("Calling _deserialize_response... <10>")

            response, content = await asyncio.create_task(self._deserialize_response(part.get_payload()))

            responses.append(json.loads(content.encode('utf-8')))

        return responses

    def _header_to_id(self, header):
        if header[0] != "<" or header[-1] != ">":
            raise BatchError(f"Invalid value for Content-ID: {header}")
        if "+" not in header:
            raise BatchError(f"Invalid value for Content-ID: {header}")
        base, id_ = header[1:-1].split(" + ", 1)

        return id_

    async def _deserialize_response(self, payload):
        """Convert string into httplib2 response and content.

    Args:
      payload: string, headers and body as a string.

    Returns:
      A pair (resp, content), such as would be returned from httplib2.request.
    """
        # Strip off the status line
        status_line, payload = payload.split("\n", 1)
        protocol, status, reason = status_line.split(" ", 2)

        # Parse the rest of the response
        parser = FeedParser()
        parser.feed(payload)
        msg = parser.close()
        msg["status"] = status

        # Create httplib2.Response from the parsed headers.
        resp = httplib2.Response(msg)
        resp.reason = reason
        resp.version = int(protocol.split("/", 1)[1].replace(".", ""))

        content = payload.split("\r\n\r\n", 1)[1]

        return resp, content
