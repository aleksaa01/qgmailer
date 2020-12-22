from googleapis.gmail.connection import GConnection
from googleapis.people.connection import PConnection

from services.event import APIEvent, IPC_SHUTDOWN
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.feedparser import FeedParser
from email.generator import Generator
from urllib.parse import urlparse, urlunparse
from io import StringIO
from googleapis.gmail.gparser import extract_body

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

TOKEN_CACHE = {}

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
    logger.info("\trequest_len_size parsed...")

    raw_data = b''
    while len(raw_data) < request_len_size:
        chunk = await reader.read(request_len_size - len(raw_data))
        if len(chunk) == 0:
            logger.info("Unable to read, connection has been closed...")
            writer.close()
            await writer.wait_closed()
        raw_data += chunk
    request_len = int(raw_data.decode('utf-8'))
    logger.info("\trequest_len parsed...")

    raw_data = []
    received_data = 0
    while received_data < request_len:
        chunk = await reader.read(min(MAX_READ_BUF, request_len - received_data))
        received_data += len(chunk)
        raw_data.append(chunk)

    logger.info("\trequest parsed...")

    api_event = pickle.loads(b''.join(raw_data))
    logger.info("Returning from parse coroutine.")
    return api_event


async def write(data, writer):
    logger = multiprocessing.get_logger()

    t = time.perf_counter()

    response_data = pickle.dumps(data)
    response_data_size = str(len(response_data))
    size_len = chr(len(response_data_size))
    raw_data = size_len.encode('utf-8') + response_data_size.encode('utf-8') + response_data

    logger.info(f"Sending response back(response_data: {len(response_data)}, "
                f"response_data_size: {response_data_size}, size_len: {size_len}, len(raw_data): {len(raw_data)})...")
    writer.write(raw_data)
    await writer.drain()
    tt = time.perf_counter()
    logger.info(f"Response sent in {tt - t} seconds !")


def create_api_task(con, con_list, func, *args, **kwargs):
    if len(con_list) == 0:
        con_list.append(con.acquire())

    resource = con_list.pop()
    return asyncio.create_task(func(resource, *args, **kwargs)), resource


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

    api_requests = {}
    read_task = None
    api_tasks = []
    while True:
        if read_task is None:
            logger.info("Created new task for parsing input data. <1>")
            read_task = asyncio.create_task(parse(reader, writer))
        elif read_task.done():
            api_event = read_task.result()
            if api_event.value == IPC_SHUTDOWN:
                logger.info("Received IPC_SHUTDOWN. Shutting down...")
                writer.close()
                await writer.wait_closed()
                return
            read_task = None

            query = CATEGORY_TO_QUERY.get(api_event.category)
            con_type = ''
            if query:
                token = TOKEN_CACHE.get(query, '')
                con_type = 'gmail'
                api_task, resource = create_api_task(gmail_conn, gconn_list, fetch_messages, query, page_token=token)
            elif api_event.category == 'send_email':
                con_type = 'gmail'
                api_task, resource = create_api_task(gmail_conn, gconn_list, send_email, api_event.value)
            elif api_event.category == 'email_content':
                con_type = 'gmail'
                api_task, resource = create_api_task(gmail_conn, gconn_list, fetch_email, api_event.value)
            elif api_event.category == 'contacts':
                token = TOKEN_CACHE.get('contacts', '')
                con_type = 'people'
                api_task, resource = create_api_task(people_conn, pconn_list, fetch_contacts, page_token=token)
            elif api_event.category == 'remove_contact':
                con_type = 'people'
                api_task, resource = create_api_task(people_conn, pconn_list, remove_contact, api_event.value)

            api_tasks.append(api_task)
            conn_list = gconn_list if con_type == 'gmail' else pconn_list
            api_requests[api_task] = (resource, api_event.event_id, conn_list)

        for task in api_tasks[:]:
            if task.done():
                logger.info("Api task done.")
                resource, event_id, conn_list = api_requests[task]
                conn_list.append(resource)
                response_api_event = APIEvent(event_id, value=task.result())
                logger.info(f"Creating task for IPC write(ID: {event_id})... <11>")
                await write(response_api_event, writer)
                logger.info("Write over. Remove task from api_tasks...")
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


async def fetch_messages(resource, query, headers=None, msg_format='metadata', max_results=10, page_token=''):
    logger = multiprocessing.get_logger()

    if page_token == 'END':
        logger.info(f'NO MORE MESSAGES TO FETCH(query:{query})')
        return []

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

    # Update token
    token = response_data.get('nextPageToken')
    TOKEN_CACHE[query] = token or 'END'

    batch = BatchApiRequest()
    messages = response_data.get('messages')
    if messages:
        for msg in messages:
            http_request = resource.users().messages().get(
                id=msg['id'], userId='me', format=msg_format, metadataHeaders=['From', 'Subject']
            )
            batch.add(http_request)
        logger.info("Calling execute... <6>")
        t1, p1 = time.time(), time.perf_counter()
        messages = await asyncio.create_task(batch.execute(headers['authorization']))
        t2, p2 = time.time(), time.perf_counter()
        logger.info(f"Got responses back. t2 - t1, p2 - p1: {t2 - t1}, {p2 - p1}")
        logger.info(f"First response: {messages[0]}")
    else:
        messages = []

    for msg in messages:
        internal_timestamp = int(msg.get('internalDate')) / 1000
        date = datetime.datetime.fromtimestamp(internal_timestamp).strftime('%b %d')
        sender = ''
        for field in msg.get('payload').get('headers'):
            if field.get('name').lower() == 'from':
                sender = field.get('value').split('<')[0]
                break
        snippet = msg.get('snippet')
        msg['email_field'] = f'{date}   \u25CF   {sender}   \u25CF   {snippet}'

    return messages


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


async def send_email(resource, message):
    logger = multiprocessing.get_logger()
    logger.info('In send_email...')

    http = resource.users().messages().send(userId='me', body=message)

    headers = http.headers
    if "content-length" not in headers:
        headers["content-length"] = str(http.body_size)

    try:
        logger.info("Calling validate_http...<3>")
        await asyncio.create_task(validate_http(http, headers))
        t1, p1 = time.time(), time.perf_counter()
        async with aiohttp.ClientSession() as session:
            async with session.post(url=http.uri, data=http.body, headers=headers) as response:
                if 200 <= response.status < 300:
                    response_data = json.loads(await response.text(encoding='utf-8'))
                else:
                    raise Exception("Failed to get data back. Response status: ", response.status)
        t2, p2 = time.time(), time.perf_counter()
        logger.info(f"Time lapse for sending an email with the Gmail-API(t, p): {t2 - t1}, {p2 - p1}")
    except Exception as err:
        logger.warning(f"Encountered an exception: {err}")
        raise Exception

    return response_data


async def fetch_contacts(resource, fields=None, max_results=10, page_token=''):
    logger = multiprocessing.get_logger()
    logger.info("In fetch_contacts...")

    if page_token == 'END':
        logger.info(f'NO MORE CONTACTS TO FETCH')
        return []

    if fields is None:
        fields = 'names,emailAddresses'

    http = resource.people().connections().list(resourceName='people/me', personFields=fields,
                                                pageSize=max_results, pageToken=page_token)
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
        logger.info(f"Time lapse for fetching list of contacts from People-API(t, p): {t2 - t1}, {p2 - p1}")
    except Exception as err:
        logger.warning(f"Encountered an exception: {err}")
        raise Exception

    token = response_data.get('nextPageToken')
    TOKEN_CACHE['contacts'] = token or 'END'

    logger.info("Extracting contacts...")
    contacts = []
    for con in response_data.get('connections', []):
        name = ''
        email = ''
        names = con.get('names', [])
        emails = con.get('emailAddresses', [])
        if names:
            name = names[0]['displayName']
        if emails:
            email = emails[0]['value']

        contacts.append({'name': name, 'email': email, 'resourceName': con.get('resourceName'), 'etag': con.get('etag')})
    logger.info("Contacts extracted.")
    return contacts


async def fetch_email(resource, email_id):
    logger = multiprocessing.get_logger()
    logger.info(f'In fetch_email(email_id:{email_id})')

    http = resource.users().messages().get(id=email_id, userId='me', format='raw')

    headers = http.headers
    if "content-length" not in headers:
        headers["content-length"] = str(http.body_size)

    try:
        logger.info("Calling validate_http...<3>")
        await asyncio.create_task(validate_http(http, headers))
        t1, p1 = time.time(), time.perf_counter()
        async with aiohttp.ClientSession() as session:
            async with session.get(url=http.uri, headers=headers) as response:
                if 200 <= response.status < 300:
                    response_data = json.loads(await response.text(encoding='utf-8'))
                else:
                    raise Exception("Failed to get data back. Response status: ", response.status)
        t2, p2 = time.time(), time.perf_counter()
        logger.info(f"Time lapse for fetching email from Gmail-API(t, p): {t2 - t1}, {p2 - p1}")
    except Exception as err:
        logger.warning(f"Encountered an exception: {err}")
        raise Exception

    email = extract_body(response_data['raw'])
    return email


async def remove_contact(resource, resource_name):
    logger = multiprocessing.get_logger()
    logger.info(f"Removing contact: {resource_name}")

    http = resource.people().deleteContact(resourceName=resource_name)

    headers = http.headers
    if "content-length" not in headers:
        headers["content-length"] = str(http.body_size)

    try:
        logger.info("Calling validate_http... <3>")
        await asyncio.create_task(validate_http(http, headers))
        t1, p1 = time.time(), time.perf_counter()
        async with aiohttp.ClientSession() as session:
            async with session.delete(url=http.uri, data=http.body, headers=headers) as response:
                if 200 <= response.status < 300:
                    response_data = json.loads(await response.text(encoding='utf-8'))
                else:
                    response_data = await response.text(encoding='utf-8')
                    raise Exception("Failed to get data back. Response status: ", response.status)
        t2, p2 = time.time(), time.perf_counter()
        logger.info(f"Time lapse for fetching list of contacts from People-API(t, p): {t2 - t1}, {p2 - p1}")
    except Exception as err:
        logger.warning(f"Handling an exception: {err}. Error data: {response_data}. Reporting an error...")
        return {'error': response_data}

    logger.info(f"Contact removed.")
    return {}
