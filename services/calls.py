from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.feedparser import FeedParser
from email.generator import Generator
from urllib.parse import urlparse, urlunparse
from io import StringIO
from html import unescape as html_unescape
from googleapis.gmail.gparser import extract_body
from googleapis.gmail.labels import *
from googleapis.gmail.history import HistoryRecord, parse_history_record
from logs.loggers import default_logger

import asyncio
import aiohttp
import uuid
import urllib
import httplib2
import time
import datetime
import json

LOG = default_logger()

LABEL_ID_TO_QUERY = {
    LABEL_ID_PERSONAL: 'in:personal',
    LABEL_ID_UPDATES: 'in:updates',
    LABEL_ID_SOCIAL: 'in:social',
    LABEL_ID_PROMOTIONS: 'in:promotions',
    LABEL_ID_SENT: 'in:sent',
    LABEL_ID_TRASH: 'in:trash',
}

# This token cache includes tokens from api calls and creds that store bearer tokens
TOKEN_CACHE = {}
GMAIL_TOKEN_ID = 'g-creds'
PEOPLE_TOKEN_ID = 'p-creds'


async def send_request(session_request_method, http=None, **kwargs):
    """
    General function for sending requests.
    :returns tuple(str: plaintext response data, bool: error flag)
    """
    if http is not None:
        url = http.uri
        headers = http.headers
        if 'content-length' not in headers:
            headers['content-length'] = str(http.body_size)
        await asyncio.create_task(validate_http(http, headers))
    else:
        url = kwargs.get('url')
        headers = kwargs.get('headers')
        token_id = kwargs.get('token_id')

    backoff = 1
    while True:
        async with session_request_method(url=url, headers=headers, **kwargs) as response:
            status = response.status
            if 200 <= status < 300:
                return await response.text(encoding='utf-8'), False
            elif status == 403:
                LOG.warning(f"Rate limit exceeded, waiting {backoff} seconds.")
                await asyncio.sleep(backoff)
                backoff *= 2
                if backoff > 32:
                    return await response.text(encoding='utf-8'), True
            elif status == 401:
                LOG.warning("send_request: 401 error encountered. Refreshing the token...")
                if http is not None:
                    await asyncio.create_task(validate_http(http, headers))
                else:
                    token = await asyncio.create_task(get_cached_token(token_id))
                    headers['authorization'] = token
            else:
                LOG.error("Unknown error in send_request, status:", status)
                return await response.text(encoding='utf-8'), True


async def refresh_token(credentials):
    """Function for refreshing access and refresh tokens, regardless of the api type."""
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

    LOG.info("Getting access_token... <5>")
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
    LOG.info(f"Time lapse for getting access_token from {url}: {t2 - t1}, {p2 - p1}")


async def validate_http(http, headers):
    credentials = http.http.credentials
    # check if creds are valid, and call refresh_token if they are not
    if credentials.token is None or not credentials.expired:
        method_id = http.methodId
        if method_id.startswith('gmail'):
            cached_creds = TOKEN_CACHE.get(GMAIL_TOKEN_ID)
        elif method_id.startswith('people'):
            cached_creds = TOKEN_CACHE.get(PEOPLE_TOKEN_ID)
        else:
            raise ValueError(f'Unknown api/api-method: {method_id}')

        if cached_creds and cached_creds.token and not cached_creds.expired:
            credentials = cached_creds
        else:
            LOG.info(f"Calling refresh_token... (Api method-id:{method_id}) <4>")
            await asyncio.create_task(refresh_token(credentials))
            if method_id.startswith('gmail'):
                TOKEN_CACHE[GMAIL_TOKEN_ID] = credentials
            elif method_id.startswith('people'):
                TOKEN_CACHE[PEOPLE_TOKEN_ID] = credentials
    headers['authorization'] = 'Bearer {}'.format(credentials.token)
    return


async def get_cached_token(token_id):
    creds = TOKEN_CACHE.get(token_id)
    if creds and creds.token and not creds.expired:
        pass
    else:
        LOG.info("Token expired, calling refresh_token...")
        await asyncio.create_task(refresh_token(creds))
        TOKEN_CACHE[token_id] = creds
    return 'Bearer {}'.format(creds.token)


async def fetch_messages(resource, label_id, max_results, headers=None, msg_format='metadata', page_token=''):
    query = LABEL_ID_TO_QUERY[label_id]
    page_token = page_token or TOKEN_CACHE.get(query, '')
    if page_token == 'END':
        LOG.info(f'NO MORE MESSAGES TO FETCH(query:{query})')
        return {'label_id': label_id, 'emails': []}

    if headers is None:
        headers = ['From', 'Subject']

    http = resource.users().messages().list(userId='me', maxResults=max_results, q=query, pageToken=page_token)

    p1 = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        LOG.debug("CALLING send_request FUNCTION...")
        pp1 = time.perf_counter()
        response, err_flag = await asyncio.create_task(send_request(session.get, http))
        pp2 = time.perf_counter()
        LOG.debug(f"FUNCTION send_request FINISHED, execution time: {pp2 - pp1}.")
        if err_flag is False:
            response_data = json.loads(response)
        else:
            response_data = response
    p2 = time.perf_counter()
    LOG.info(f"List of emails fetched in: {p2 - p1} seconds.")
    if err_flag:
        LOG.error(f"Error data: {response_data}. Reporting an error...")
        return {'label_id': label_id, 'emails': [], 'error': response_data}

    # Update token
    token = response_data.get('nextPageToken')
    TOKEN_CACHE[query] = token or 'END'

    batch = BatchApiRequest()
    messages = response_data.get('messages')
    if messages:
        if label_id == LABEL_ID_SENT:
            uri = 'https://gmail.googleapis.com/gmail/v1/users/me/messages/{0}?format=metadata&metadataHeaders=To&metadataHeaders=Subject&alt=json'
        else:
            uri = 'https://gmail.googleapis.com/gmail/v1/users/me/messages/{0}?format=metadata&metadataHeaders=From&metadataHeaders=Subject&alt=json'
        method = 'GET'
        essential_headers = {'accept': 'application/json', 'accept-encoding': 'gzip, deflate',
                             'user-agent': '(gzip)', 'x-goog-api-client': 'gdcl/1.12.8 gl-python/3.8.5'}
        p1 = time.perf_counter()
        for msg in messages:
            resource_uri = uri.format(msg['id'])
            http_request = OptimizedHttpRequest(resource_uri, method, essential_headers, None)
            batch.add(http_request)
        p2 = time.perf_counter()
        LOG.info(f"Messages batched in: {p2 - p1} seconds.")
        LOG.info("Calling execute... <6>")
        p1 = time.perf_counter()
        try:
            messages = await asyncio.create_task(batch.execute(http.headers['authorization']))
        except BatchError as err:
            return {'label_id': label_id, 'email': [], 'error': err}
        p2 = time.perf_counter()
        LOG.info(f"BatchApiRequest.execute() finished in: {p2 - p1} seconds.")
    else:
        messages = []

    for msg in messages:
        internal_timestamp = int(msg.get('internalDate')) / 1000
        # TODO: Dates of the current year should be formatted like: Dec 13,
        #   but dates from previous years should be formatted like: Feb 17, 2009
        date = datetime.datetime.fromtimestamp(internal_timestamp).strftime('%b %d')
        sender = None
        recipient = None
        subject = '(no subject)'
        for field in msg.get('payload').get('headers'):
            field_name = field.get('name').lower()
            if field_name == 'from':
                sender = field.get('value').split('<')[0]
            elif field_name == 'to':
                recipient = field.get('value').split('<')[0].split('@')[0]
            elif field_name == 'subject':
                subject = field.get('value') or subject
        snippet = html_unescape(msg.get('snippet'))
        unread = GMAIL_LABEL_UNREAD in msg.get('labelIds')
        msg['email_field'] = [sender or recipient, subject, snippet, date, unread]

    return {'label_id': label_id, 'emails': messages}


class OptimizedHttpRequest(object):
    def __init__(self, uri, method, headers, body):
        self.uri = uri
        self.method = method
        self.headers = headers.copy()
        self.body = body


class BatchError(Exception): pass


class BatchApiRequest(object):
    MAX_BATCH_LIMIT = 100

    def __init__(self):
        self.requests = []
        # List of successfully completed responses.
        self.completed_responses = []
        self._batch_uri = 'https://gmail.googleapis.com/batch'
        self._base_id = uuid.uuid4()

        self.access_token = None
        self.backoff = 1

    def add(self, http_request):
        if len(self.requests) > self.MAX_BATCH_LIMIT:
            raise BatchError(
                f"Exceeded the maximum of {self.MAX_BATCH_LIMIT} calls in a single batch request."
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

    async def execute(self, access_token=None):
        if access_token is None:
            if self.access_token is None:
                raise ValueError("Access token is not specified")
            access_token = self.access_token
        else:
            self.access_token = access_token
        """Validated credentials before calling this coroutine."""
        message = MIMEMultipart("mixed")
        # Message should not write out it's own headers.
        setattr(message, "_write_headers", lambda arg: None)

        LOG.info("Building a message...")
        p1 = time.perf_counter()
        for rid, request in enumerate(self.requests):
            msg_part = MIMENonMultipart("application", "http")
            msg_part["Content-Transfer-Encoding"] = "binary"
            msg_part["Content-ID"] = self._id_to_header(str(rid))

            body = await asyncio.create_task(self._serialize_request(request))
            msg_part.set_payload(body)
            message.attach(msg_part)
        p2 = time.perf_counter()
        LOG.info(f"Message build finished in: {p2 - p1} seconds.")

        LOG.info("Flattening the message...")
        fp = StringIO()
        g = Generator(fp, mangle_from_=False)
        g.flatten(message, unixfrom=False)
        body = fp.getvalue()

        headers = {}
        headers["content-type"] = f'multipart/mixed; boundary="{message.get_boundary()}"'
        headers['authorization'] = access_token

        LOG.info("Sending batch request... <8>")
        p1 = time.perf_counter()
        backoff = 1
        async with aiohttp.ClientSession() as session:
            async with session.post(url=self._batch_uri, data=body, headers=headers) as response:
                status = response.status
                if 200 <= status < 300:
                    content = await response.text(encoding='utf-8')
                elif status == 403 or status == 429:
                    LOG.warning(f"Rate limit exceeded, waiting {backoff} seconds.")
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    if backoff > 32:
                        data = await response.text(encoding='utf-8')
                        LOG.error(f"Repeated rate limit errors. Last error: {data}")
                        raise BatchError(f"{data}")
                elif status == 401:
                    LOG.warning("BatchApiRequest.execute: 401 error encountered. Refreshing the token...")
                    headers['authorization'] = await asyncio.create_task(get_cached_token(GMAIL_TOKEN_ID))
                else:
                    data = await response.text(encoding='utf-8')
                    LOG.warning(f"Unhandled error in BatchApiRequest.execute. Error: {data}")
                    raise BatchError(f"{data}")
        p2 = time.perf_counter()
        LOG.info(f"Batch response fetched in : {p2 - p1} seconds.")

        LOG.info("Calling parse_response... <9>")
        await asyncio.create_task(self.handle_response(response, content))
        if len(self.requests) > 0:
            LOG.info("Some tasks FAILED, calling execute again.")
            await asyncio.create_task(self.execute())
        return self.completed_responses

    async def handle_response(self, response, content):
        LOG.info("Parsing response...")

        header = f"content-type: {response.headers['content-type']}\r\n\r\n"
        for_parser = header + content
        parser = FeedParser()
        parser.feed(for_parser)
        mime_response = parser.close()

        failed_requests = []
        # Separation of the multipart response message.
        error_401, error_403, error_429 = False, False, False
        for part in mime_response.get_payload():
            http_request_idx = int(self._header_to_id(part["Content-ID"]))
            http_request = self.requests[http_request_idx]

            response, content = await asyncio.create_task(self._deserialize_response(part.get_payload()))
            parsed_response = json.loads(content)
            if isinstance(parsed_response, dict) and 'error' in parsed_response:
                error_code = parsed_response['error']['code']
                if error_code == 429: error_429 = True
                elif error_code == 403: error_403 = True
                elif error_code == 401: error_401 = True
                else:
                    LOG.error(f"BatchApiRequest: Unhandled error in one of the responses: {parsed_response}")
                    continue
                failed_requests.append(http_request)
            else:
                self.completed_responses.append(parsed_response)

        self.requests = failed_requests
        if error_401:
            self.access_token = await asyncio.create_task(get_cached_token(GMAIL_TOKEN_ID))
        if error_403 or error_429:
            LOG.warning(f"Rate limit exceeded, waiting {self.backoff} seconds.")
            await asyncio.sleep(self.backoff)
            self.backoff *= 2
            if self.backoff > 32:
                # TODO: Backoff is too high, just throw an error.
                pass

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


async def send_email(resource, label_id, email_msg):
    LOG.info('In send_email...')

    http = resource.users().messages().send(userId='me', body=email_msg)

    p1 = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.post, http, data=http.body))
        if err_flag is False:
            response_data = json.loads(response)
        else:
            response_data = response
    p2 = time.perf_counter()
    LOG.info(f"Sent an email in: {p2 - p1} seconds.")
    if err_flag:
        LOG.error(f"Error data: {response_data}. Reporting an error...")
        return {'label_id': label_id, 'email': {}, 'error': response_data}

    http = resource.users().messages().get(userId='me', id=response_data.get('id'), format='metadata',
                                           metadataHeaders=['To', 'Subject'])

    p1 = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.get, http))
        if err_flag is False:
            response_data = json.loads(response)
        else:
            response_data = response
    p2 = time.perf_counter()
    LOG.info(f"Email fetched in: {p2 - p1} seconds.")
    if err_flag:
        LOG.error(f"Error data: {response_data}. Reporting an error...")
        return {'label_id': label_id, 'email': {}, 'error': response_data}

    internal_timestamp = int(response_data.get('internalDate')) / 1000
    # TODO: Dates of the current year should be formatted like: Dec 13,
    #   but dates from previous years should be formatted like: Feb 17, 2009
    date = datetime.datetime.fromtimestamp(internal_timestamp).strftime('%b %d')
    recipient = None
    subject = '(no subject)'
    for field in response_data.get('payload').get('headers'):
        field_name = field.get('name').lower()
        if field_name == 'to':
            recipient = field.get('value').split('<')[0].split('@')[0]
        elif field_name == 'subject':
            subject = field.get('value') or subject
    snippet = html_unescape(response_data.get('snippet'))
    unread = GMAIL_LABEL_UNREAD in response_data.get('labelIds')
    response_data['email_field'] = [recipient, subject, snippet, date, unread]

    return {'label_id': label_id, 'email': response_data}


async def fetch_contacts(resource, max_results, fields=None, page_token=''):
    LOG.info("In fetch_contacts...")

    page_token = page_token or TOKEN_CACHE.get('contacts', '')
    if page_token == 'END':
        LOG.info(f'NO MORE CONTACTS TO FETCH')
        return {'contacts': []}

    if fields is None:
        fields = 'names,emailAddresses'

    http = resource.people().connections().list(resourceName='people/me', personFields=fields,
                                                pageSize=max_results, pageToken=page_token)

    p1 = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.get, http))
        if err_flag is False:
            response_data = json.loads(response)
        else:
            response_data = response
    p2 = time.perf_counter()
    LOG.info(f"List of contacts fetched in: {p2 - p1} seconds.")
    if err_flag:
        LOG.error(f"Error data: {response_data}. Reporting an error...")
        return {'contacts': [], 'total_contacts': 0, 'error': response_data}

    token = response_data.get('nextPageToken')
    TOKEN_CACHE['contacts'] = token or 'END'

    LOG.info("Extracting contacts...")
    total_contacts = response_data.get('totalItems')
    LOG.debug(F"TOTAL NUMBER OF ITEMS IN connections.list is: {total_contacts}")
    contacts = []
    # givenName = first name; familyName = last name; displayName = maybe both;
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
    return {'contacts': contacts, 'total_contacts': total_contacts}


async def fetch_email(resource, email_id):
    LOG.info(f'In fetch_email(email_id:{email_id})')

    http = resource.users().messages().get(id=email_id, userId='me', format='raw')

    p1 = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.get, http))
        if err_flag is False:
            response_data = json.loads(response)
        else:
            response_data = response
    p2 = time.perf_counter()
    LOG.info(f"Email fetched in: {p2 - p1} seconds.")
    if err_flag:
        LOG.error(f"Error data: {response_data}. Reporting an error...")
        return {'body': '', 'attachments': '', 'error': response_data}

    body, attachments = extract_body(response_data['raw'])
    return {'body': body, 'attachments': attachments}


async def add_contact(resource, name, email):
    LOG.info(f"Adding contact(name/email): {name}/{email}")

    # givenName = first name; familyName = last name; displayName = maybe both;
    body = {'names': [{'givenName': name}], 'emailAddresses': [{'value': email}]}
    http = resource.people().createContact(body=body)

    p1 = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.post, http, data=http.body))
        if err_flag is False:
            response_data = json.loads(response)
        else:
            response_data = response
    p2 = time.perf_counter()
    LOG.info(f"Contact added in: {p2 - p1} seconds.")
    if err_flag:
        LOG.error(f"Error data: {response_data}. Reporting an error...")
        return {'name': '', 'email': '', 'resourceName': '', 'etag': '', 'error': response_data}

    name = ''
    email = ''
    names = response_data.get('names', [])
    emails = response_data.get('emailAddresses', [])
    if names:
        # givenName = first name; familyName = last name; displayName = maybe both;
        # So add here either also familyName, or just look for displayName
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

    p1 = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.delete, http, data=http.body))
        if err_flag is False:
            response_data = json.loads(response)
        else:
            response_data = response
    p2 = time.perf_counter()
    LOG.info(f"Contact removed in: {p2 - p1} seconds.")
    if err_flag:
        LOG.error(f"Error data: {response_data}. Reporting an error...")
        return {'error': response_data}

    LOG.info(f"Contact removed.")
    return {}


async def trash_email(resource, email, from_lbl_id, to_lbl_id):
    LOG.debug(f"In trash_email. Trashing an email from: {from_lbl_id}.")

    # Response only contains: id, threadId, labelIds
    http = resource.users().messages().trash(userId='me', id=email.get('id'))

    p1 = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.post, http, data=http.body))
        if err_flag is False:
            response_data = json.loads(response)
        else:
            response_data = response
    p2 = time.perf_counter()
    LOG.info(f"Email sent to trash in: {p2 - p1} seconds.")
    if err_flag:
        LOG.error(f"Error data: {response_data}. Reporting an error...")
        return {'email': email, 'from_lbl_id': from_lbl_id, 'to_lbl_id': LABEL_ID_TRASH, 'error': response_data}

    email['labelIds'] = response_data['labelIds']

    return {'email': email, 'from_lbl_id': from_lbl_id, 'to_lbl_id': LABEL_ID_TRASH}


async def untrash_email(resource, email, from_lbl_id, to_lbl_id):
    LOG.debug("In untrash_email")

    http = resource.users().messages().untrash(userId='me', id=email.get('id'))

    p1 = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.post, http, data=http.body))
        if err_flag is False:
            response_data = json.loads(response)
        else:
            response_data = response
    p2 = time.perf_counter()
    LOG.info(f"Email restored from trash in: {p2 - p1} seconds.")
    if err_flag:
        LOG.error(f"Error data: {response_data}. Reporting an error...")
        # In case of an error passing to_lbl_id=0 means we don't know to which label
        # should this email be restored to.
        return {'email': email, 'from_lbl_id': LABEL_ID_TRASH, 'to_lbl_id': 0, 'error': response_data}

    email['labelIds'] = response_data['labelIds']

    to_label_id = 0
    for lbl_id in response_data['labelIds']:
        if lbl_id in LABEL_TO_LABEL_ID:
            to_label_id = LABEL_TO_LABEL_ID[lbl_id]
            break
    assert to_label_id != 0

    return {'email': email, 'from_lbl_id': LABEL_ID_TRASH, 'to_lbl_id': to_label_id}


async def delete_email(resource, label_id, id):
    LOG.info(f"In delete_email(label_id: {label_id})")

    http = resource.users().messages().delete(userId='me', id=id)

    p1 = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.delete, http, data=http.body))
        # If email was successfully deleted, response body will be emtpy
        response_data = response
    p2 = time.perf_counter()
    LOG.info(f"Email deleted in: {p2 - p1} seconds.")
    if err_flag:
        LOG.error(f"Error data: {response_data}. Reporting an error...")
        return {'label_id': label_id, 'error': response_data}

    return {'label_id': label_id}


async def edit_contact(resource, name, email, contact):
    LOG.info(f"In edit_contact(name, email): {name}, {email}")

    resourceName = contact.get('resourceName')
    etag = contact.get('etag')

    body = {
        # givenName = first name; familyName = last name; displayName = maybe both;
        # When I add ability to enter the last name too, I should add familyName to names,
        # not put displayName instead.
        'names': [{'givenName': name}],
        'emailAddresses': [{'value': email}],
        'etag': etag,
        'metadata': {
            'sources': [
                {'etag': etag, 'type': 'CONTACT'}
            ]
        }
    }
    http = resource.people().updateContact(resourceName=resourceName, body=body, updatePersonFields='names,emailAddresses')

    p1 = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.patch, http, data=http.body))
        if err_flag is False:
            response_data = json.loads(response)
        else:
            response_data = response
    p2 = time.perf_counter()
    LOG.info(f"Contact edited in: {p2 - p1} seconds.")
    if err_flag:
        LOG.error(f"Error data: {response_data}. Reporting an error...")
        return {'name': name, 'email': email, 'resourceName': resourceName, 'etag': etag, 'error': response_data}

    # So my understanding is that you have some property name about a particular contact, like "names" for example.
    # And that property can be consisted of multiple data from multiple sources(aka APIs). And the way you check
    # this is by looking at names[index]['metadata']['source']['type']. So in this context, I am only interested
    # in CONTACT source-type, I think.
    names = response_data['names']
    emails = response_data['emailAddresses']
    # givenName = first name; familyName = last name; displayName = maybe both;
    name = names[0]['displayName']
    email = emails[0]['value']
    resourceName = response_data['resourceName']
    etag = response_data['etag']

    return {'name': name, 'email': email, 'resourceName': resourceName, 'etag': etag}


async def short_sync(resource, start_history_id, max_results,
                     types=['labelAdded', 'labelRemoved', 'messageAdded', 'messageDeleted']):
    LOG.debug("In short_sync async function...")

    http = resource.users().history().list(
        userId='me', maxResults=max_results, startHistoryId=start_history_id, historyTypes=types)

    all_history_records = []
    LOG.debug("FETCHING HISTORY RECORDS...")
    while True:
        async with aiohttp.ClientSession() as session:
            response, err_flag = await asyncio.create_task(send_request(session.get, http))
            if err_flag is False:
                response_data = json.loads(response)
            else:
                response_data = response
        if err_flag:
            LOG.error(f"Error data: {response_data}. Reporting an error...")
            return {'events': [], 'last_history_id': '', 'error': response_data}

        LOG.debug(f"RESPONSE DATA: {response_data}")
        all_history_records.extend(response_data.get('history', []))
        token = response_data.get('nextPageToken', '')
        if len(token) == 0:
            last_history_id = response_data.get('historyId')
            LOG.info(f"LATEST HISTORY ID: {last_history_id}")
            LOG.info(f"NUMBER OF HISTORY RECORDS: {len(all_history_records)}")
            break

        # Increase the amount of history-records to be fetched, but limit it to 100(each costs 2 quota)
        max_results = min(100, max_results + max_results)
        http = resource.users().history().list(
            userId='me', maxResults=max_results, startHistoryId=start_history_id,
            historyTypes=types, pageToken=token)

    # Now we have all history records in all_history_records
    # And we have the latest historyId in last_history_id

    history_records = {}
    LOG.debug("PARSING HISTORY RECORDS...")
    for hrecord in all_history_records:
        parse_history_record(hrecord, history_records)

    LOG.debug(f"HISTORY RECORDS AFTER PARSING: {history_records}")

    # Now fetch data for all emails in history records.
    messages = []
    if history_records:
        batch_request = BatchApiRequest()
        uri_sent = 'https://gmail.googleapis.com/gmail/v1/users/me/messages/{0}?' \
                   'format=metadata&metadataHeaders=To&metadataHeaders=Subject&alt=json'
        uri_inbox = 'https://gmail.googleapis.com/gmail/v1/users/me/messages/{0}?' \
                    'format=metadata&metadataHeaders=From&metadataHeaders=Subject&alt=json'
        method = 'GET'
        essential_headers = {'accept': 'application/json', 'accept-encoding': 'gzip, deflate',
                   'user-agent': '(gzip)', 'x-goog-api-client': 'gdcl/1.12.8 gl-python/3.8.5'}

        for history_record in history_records.values():
            if history_record.action != HistoryRecord.ACTION_DELETE:
                if history_record.label_type == HistoryRecord.LABEL_TYPE_SENT:
                    resource_uri = uri_sent.format(history_record.message_id)
                else:
                    resource_uri = uri_inbox.format(history_record.message_id)

                http = OptimizedHttpRequest(resource_uri, method, essential_headers, None)
                batch_request.add(http)

        if len(batch_request.requests) > 0:
            LOG.debug("SENDING A BATCH REQUEST FOR ALL HISTORY RECORDS...")
            try:
                messages = await asyncio.create_task(
                    batch_request.execute(await asyncio.create_task(get_cached_token(GMAIL_TOKEN_ID))))
            except BatchError as err:
                return {'history_records': [], 'last_history_id': '', 'error': err}

    LOG.debug("PARSING ALL MESSAGES, AND ADDING THEM TO CORRESPONDING HISTORY RECORDS...")
    for msg in messages:
        internal_timestamp = int(msg.get('internalDate')) / 1000
        date = datetime.datetime.fromtimestamp(internal_timestamp).strftime('%b %d')
        sender = None
        recipient = None
        subject = '(no subject)'
        for field in msg.get('payload').get('headers'):
            field_name = field.get('name').lower()
            if field_name == 'from':
                sender = field.get('value').split('<')[0]
            elif field_name == 'to':
                recipient = field.get('value').split('<')[0].split('@')[0]
            elif field_name == 'subject':
                subject = field.get('value') or subject
        snippet = html_unescape(msg.get('snippet'))
        unread = GMAIL_LABEL_UNREAD in msg.get('labelIds')
        msg['email_field'] = [sender or recipient, subject, snippet, date, unread]

        his_record = history_records[msg['id']]
        his_record.set_email(msg)

    LOG.debug(f"ALL HISTORY RECORDS AFTER THEY'VE BEEN FETCHED: {history_records}")
    return {'history_records': list(history_records.values()), 'last_history_id': last_history_id}


async def total_messages_with_label_id(resource, label_id):
    label = LABEL_ID_TO_LABEL[label_id]
    http = resource.users().labels().get(userId='me', id=label)
    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.get, http))

    if err_flag is True:
        LOG.error(f"Error data: {response}. Reporting an error...")
        return {'label_id': label_id, 'num_messages': 0, 'error': response}

    response_data = json.loads(response)
    total_messages = response_data['messagesTotal']
    LOG.debug(f"TOTAL NUMBER OF MESSAGES WITH LABEL {label} = {total_messages}")
    return {'label_id': label_id, 'num_messages': total_messages}


async def modify_labels(resource, email_id, to_add, to_remove):
    body = {
        "removeLabelIds": list(to_remove),
        "addLabelIds": list(to_add)
    }
    http = resource.users().messages().modify(userId='me', id=email_id, body=body)

    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.post, http, data=http.body))

        if err_flag is True:
            LOG.error(f"Failed to modify labels. Error: {response}")
            return {}

    LOG.debug("Labels modified successfully.")
    return {}
