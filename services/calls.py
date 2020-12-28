from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.feedparser import FeedParser
from email.generator import Generator
from urllib.parse import urlparse, urlunparse
from io import StringIO
from googleapis.gmail.gparser import extract_body

import asyncio
import multiprocessing
import aiohttp
import uuid
import urllib
import httplib2
import time
import datetime
import json

LOG = multiprocessing.get_logger()

CATEGORY_TO_QUERY = {
    'personal': 'in:personal',
    'social': 'in:social',
    'promotions': 'in:promotions',
    'updates': 'in:updates',
    'sent': 'in:sent',
    'trash': 'in:trash',
}

TOKEN_CACHE = {}


async def refresh_token(credentials):
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

    LOG.info("Getting access_token from Gmail API... <5>")
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
    LOG.info(f"Time lapse for getting access_token from Gmail-API(t, p): {t2 - t1}, {p2 - p1}")


async def validate_http(http, headers):
    creds = http.http.credentials
    LOG.info(f"Creds.expired: {creds.token}, {creds.expired}")
    # check if creds are valid, and call refresh_token if they are not
    if creds.token is None or not creds.expired:
        LOG.info("Calling refresh_token... <4>")
        await asyncio.create_task(refresh_token(creds))
        headers['authorization'] = 'Bearer {}'.format(creds.token)
    return


async def fetch_messages(resource, category, headers=None, msg_format='metadata', max_results=10, page_token=''):
    query = CATEGORY_TO_QUERY[category]
    page_token = page_token or TOKEN_CACHE.get(query, '')
    if page_token == 'END':
        LOG.info(f'NO MORE MESSAGES TO FETCH(query:{query})')
        return []

    if headers is None:
        headers = ['From', 'Subject']

    http = resource.users().messages().list(userId='me', maxResults=max_results, q=query, pageToken=page_token)
    headers = http.headers
    if "content-length" not in headers:
        headers["content-length"] = str(http.body_size)

    try:
        LOG.info("Calling validate_http... <3>")
        await asyncio.create_task(validate_http(http, headers))
        t1, p1 = time.time(), time.perf_counter()
        async with aiohttp.ClientSession() as session:
            async with session.get(http.uri, headers=headers) as response:
                if 200 <= response.status < 300:
                    response_data = json.loads(await response.text(encoding='utf-8'))
                else:
                    response_data = await response.text(encoding='utf-8')
                    raise Exception("Failed to get data back. Response status: ", response.status)
        t2, p2 = time.time(), time.perf_counter()
        LOG.info(f"Time lapse for fetching list of messages from Gmail-API(t, p): {t2 - t1}, {p2 - p1}")
    except Exception as err:
        LOG.warning(f"Encountered an exception: {err}. Error data: {response_data}. Reporting an error...")
        return {'category': category, 'emails': [], 'error': response_data}

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
        LOG.info("Calling execute... <6>")
        t1, p1 = time.time(), time.perf_counter()
        messages = await asyncio.create_task(batch.execute(headers['authorization']))
        t2, p2 = time.time(), time.perf_counter()
        LOG.info(f"Got responses back. t2 - t1, p2 - p1: {t2 - t1}, {p2 - p1}")
        LOG.info(f"First response: {messages[0]}")
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

    return {'category': category, 'emails': messages}


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
        message = MIMEMultipart("mixed")
        # Message should not write out it's own headers.
        setattr(message, "_write_headers", lambda arg: None)

        LOG.info("Looping through request...")

        for rid, request in enumerate(self.requests):
            msg_part = MIMENonMultipart("application", "http")
            msg_part["Content-Transfer-Encoding"] = "binary"
            msg_part["Content-ID"] = self._id_to_header(str(rid))

            if rid == 0:
                LOG.info("Calling _serialize_request in for loop... <7>")

            body = await asyncio.create_task(self._serialize_request(request))
            msg_part.set_payload(body)
            message.attach(msg_part)

        LOG.info("Flatening message...")
        fp = StringIO()
        g = Generator(fp, mangle_from_=False)
        g.flatten(message, unixfrom=False)
        body = fp.getvalue()

        headers = {}
        headers["content-type"] = f'multipart/mixed; boundary="{message.get_boundary()}"'
        headers['authorization'] = access_token

        LOG.info("Sending request... <8>")
        t1, p1 = time.time(), time.perf_counter()
        async with aiohttp.ClientSession() as session:
            async with session.post(url=self._batch_uri, data=body, headers=headers) as response:
                if response.status < 200 or response.status >= 300:
                    raise Exception("Batch request failed. Response status: ", response.status)
                else:
                    content = await response.text(encoding='utf-8')
        t2, p2 = time.time(), time.perf_counter()
        LOG.info(f"Time lapse for getting response from Batch request(t, p): {t2 - t1}, {p2 - p1}")
        LOG.info("Calling parse_response... <9>")
        return await asyncio.create_task(self.parse_response(response, content))

    async def parse_response(self, response, content):
        LOG.info("Parsing response...")

        header = f"content-type: {response.headers['content-type']}\r\n\r\n"
        for_parser = header + content
        parser = FeedParser()
        parser.feed(for_parser)
        mime_response = parser.close()

        LOG.info(f"mime_response.is_multipart(): {mime_response.is_multipart()}")

        responses = []
        # Separation of the multipart response message.
        count = 0 # DELETE
        for part in mime_response.get_payload():
            request_id = self._header_to_id(part["Content-ID"])

            count += 1
            if count == 0:
                LOG.info("Calling _deserialize_response... <10>")

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


async def send_email(resource, email_message):
    LOG.info('In send_email...')

    http = resource.users().messages().send(userId='me', body=email_message)

    headers = http.headers
    if "content-length" not in headers:
        headers["content-length"] = str(http.body_size)

    try:
        LOG.info("Calling validate_http...<3>")
        await asyncio.create_task(validate_http(http, headers))
        t1, p1 = time.time(), time.perf_counter()
        async with aiohttp.ClientSession() as session:
            async with session.post(url=http.uri, data=http.body, headers=headers) as response:
                if 200 <= response.status < 300:
                    response_data = json.loads(await response.text(encoding='utf-8'))
                else:
                    response_data = await response.text(encoding='utf-8')
                    raise Exception("Failed to get data back. Response status: ", response.status)
        t2, p2 = time.time(), time.perf_counter()
        LOG.info(f"Time lapse for sending an email with the Gmail-API(t, p): {t2 - t1}, {p2 - p1}")
    except Exception as err:
        LOG.warning(f"Encountered an exception: {err}. Error data: {response_data}. Reporting an error...")
        return {'error': response_data}

    return {}


async def fetch_contacts(resource, fields=None, max_results=10, page_token=''):
    LOG.info("In fetch_contacts...")

    page_token = page_token or TOKEN_CACHE.get('contacts', '')
    if page_token == 'END':
        LOG.info(f'NO MORE CONTACTS TO FETCH')
        return []

    if fields is None:
        fields = 'names,emailAddresses'

    http = resource.people().connections().list(resourceName='people/me', personFields=fields,
                                                pageSize=max_results, pageToken=page_token)
    headers = http.headers
    if "content-length" not in headers:
        headers["content-length"] = str(http.body_size)

    try:
        LOG.info("Calling validate_http... <3>")
        await asyncio.create_task(validate_http(http, headers))
        t1, p1 = time.time(), time.perf_counter()
        async with aiohttp.ClientSession() as session:
            async with session.get(http.uri, headers=headers) as response:
                if 200 <= response.status < 300:
                    response_data = json.loads(await response.text(encoding='utf-8'))
                else:
                    response_data = await response.text(encoding='utf-8')
                    raise Exception("Failed to get data back. Response status: ", response.status)
        t2, p2 = time.time(), time.perf_counter()
        LOG.info(f"Time lapse for fetching list of contacts from People-API(t, p): {t2 - t1}, {p2 - p1}")
    except Exception as err:
        LOG.warning(f"Encountered an exception: {err}. Error data: {response_data}. Reporting an error...")
        return {'contacts': [], 'error': response_data}

    token = response_data.get('nextPageToken')
    TOKEN_CACHE['contacts'] = token or 'END'

    LOG.info("Extracting contacts...")
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

        contacts.append({'name': name, 'email': email,
                         'resourceName': con.get('resourceName'), 'etag': con.get('etag')})
    LOG.info("Contacts extracted.")
    return {'contacts': contacts}


async def fetch_email(resource, email_id):
    LOG.info(f'In fetch_email(email_id:{email_id})')

    http = resource.users().messages().get(id=email_id, userId='me', format='raw')

    headers = http.headers
    if "content-length" not in headers:
        headers["content-length"] = str(http.body_size)

    try:
        LOG.info("Calling validate_http...<3>")
        await asyncio.create_task(validate_http(http, headers))
        t1, p1 = time.time(), time.perf_counter()
        async with aiohttp.ClientSession() as session:
            async with session.get(url=http.uri, headers=headers) as response:
                if 200 <= response.status < 300:
                    response_data = json.loads(await response.text(encoding='utf-8'))
                else:
                    response_data = await response.text(encoding='utf-8')
                    raise Exception("Failed to get data back. Response status: ", response.status)
        t2, p2 = time.time(), time.perf_counter()
        LOG.info(f"Time lapse for fetching email from Gmail-API(t, p): {t2 - t1}, {p2 - p1}")
    except Exception as err:
        LOG.warning(f"Encountered an exception: {err}. Error data: {response_data}. Reporting an error...")
        return {'body': '', 'attachments': '', 'error': response_data}

    body, attachments = extract_body(response_data['raw'])
    return {'body': body, 'attachments': attachments}


async def add_contact(resource, name, email):
    LOG.info(f"Adding contact(name/email): {name}/{email}")

    body = {'names': [{'givenName': name, 'displayName': name}], 'emailAddresses': [{'value': email}]}
    http = resource.people().createContact(body=body)
    headers = http.headers
    if "content-length" not in headers:
        headers["content-length"] = str(http.body_size)

    try:
        LOG.info("Calling validate_http... <3>")
        await asyncio.create_task(validate_http(http, headers))
        t1, p1 = time.time(), time.perf_counter()
        async with aiohttp.ClientSession() as session:
            async with session.post(url=http.uri, data=http.body, headers=headers) as response:
                if 200 <= response.status < 300:
                    response_data = json.loads(await response.text(encoding='utf-8'))
                else:
                    response_data = await response.text(encoding='utf-8')
                    raise Exception("Failed to get data back. Response status: ", response.status)
        t2, p2 = time.time(), time.perf_counter()
        LOG.info(f"Time lapse of adding contact to People-API(t, p): {t2 - t1}, {p2 - p1}")
    except Exception as err:
        LOG.warning(f"Handling an exception: {err}. Error data: {response_data}. Reporting an error...")
        return {'name': '', 'email': '', 'resourceName': '', 'etag': '', 'error': response_data}

    name = ''
    email = ''
    names = response_data.get('names', [])
    emails = response_data.get('emailAddresses', [])
    if names:
        name = names[0]['displayName']
    if emails:
        email = emails[0]['value']

    contact = {'name': name, 'email': email,
               'resourceName': response_data.get('resourceName'), 'etag': response_data.get('etag')}

    LOG.info(f"Contact added.")
    return contact


async def remove_contact(resource, resourceName):
    LOG.info(f"Removing contact: {resourceName}")

    http = resource.people().deleteContact(resourceName=resourceName)

    headers = http.headers
    if "content-length" not in headers:
        headers["content-length"] = str(http.body_size)

    try:
        LOG.info("Calling validate_http... <3>")
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
        LOG.info(f"Time lapse of removing a contact from People-API(t, p): {t2 - t1}, {p2 - p1}")
    except Exception as err:
        LOG.warning(f"Handling an exception: {err}. Error data: {response_data}. Reporting an error...")
        return {'error': response_data}

    LOG.info(f"Contact removed.")
    return {}
