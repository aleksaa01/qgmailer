from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.feedparser import FeedParser
from email.generator import Generator
from urllib.parse import urlparse, urlunparse
from io import StringIO
from html import unescape as html_unescape
from googleapis.gmail.gparser import extract_body
from googleapis.gmail.labels import *
from googleapis.gmail.history import HistoryRecord, parse_history_record, new_parse_history_record, \
    new_HistoryRecord
from googleapis.gmail.messages import EmailMessage, idate_dtime, dtime_idate
from logs.loggers import default_logger
from persistence.db import get_app_info

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

    LOG.debug("Getting access_token... <5>")
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
            LOG.debug(f"Calling refresh_token... (Api method-id:{method_id}) <4>")
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
        LOG.info(f'All messages with label_id={label_id} have been already fetched.')
        return {'label_id': label_id, 'emails': []}

    if headers is None:
        headers = ['From', 'Subject']

    http = resource.users().messages().list(userId='me', maxResults=max_results, q=query, pageToken=page_token)

    p1 = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        pp1 = time.perf_counter()
        response, err_flag = await asyncio.create_task(send_request(session.get, http))
        pp2 = time.perf_counter()
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
        if len(self.requests) >= self.MAX_BATCH_LIMIT:
            raise BatchError(
                f"Exceeded the maximum of {self.MAX_BATCH_LIMIT} calls in a single batch request."
            )
        self.requests.append(http_request)

    def __len__(self):
        return len(self.requests)

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

        p1 = time.perf_counter()
        for rid, request in enumerate(self.requests):
            msg_part = MIMENonMultipart("application", "http")
            msg_part["Content-Transfer-Encoding"] = "binary"
            msg_part["Content-ID"] = self._id_to_header(str(rid))

            body = await asyncio.create_task(self._serialize_request(request))
            msg_part.set_payload(body)
            message.attach(msg_part)
        p2 = time.perf_counter()

        fp = StringIO()
        g = Generator(fp, mangle_from_=False)
        g.flatten(message, unixfrom=False)
        body = fp.getvalue()

        headers = {}
        headers["content-type"] = f'multipart/mixed; boundary="{message.get_boundary()}"'
        headers['authorization'] = access_token

        LOG.debug("Sending the batch request...")
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

        await asyncio.create_task(self.handle_response(response, content))
        if len(self.requests) > 0:
            LOG.warning("Some tasks FAILED, calling execute again.")
            await asyncio.create_task(self.execute())
        return self.completed_responses

    async def handle_response(self, response, content):
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
    page_token = page_token or TOKEN_CACHE.get('contacts', '')
    if page_token == 'END':
        LOG.info(f'All contacts have been already fetched.')
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
    return {'contacts': contacts, 'total_contacts': total_contacts}


async def fetch_email(resource, email_id):
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

    return contact


async def remove_contact(resource, resourceName):
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

    return {}


async def trash_email(resource, email, from_lbl_id, to_lbl_id):
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
            LOG.debug(f"LATEST HISTORY ID: {last_history_id}")
            LOG.debug(f"NUMBER OF HISTORY RECORDS: {len(all_history_records)}")
            break

        # Increase the amount of history-records to be fetched, but limit it to 100(each costs 2 quota)
        max_results = min(100, max_results + max_results)
        http = resource.users().history().list(
            userId='me', maxResults=max_results, startHistoryId=start_history_id,
            historyTypes=types, pageToken=token)

    # Now we have all history records in all_history_records
    # And we have the latest historyId in last_history_id

    history_records = {}
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
            try:
                messages = await asyncio.create_task(
                    batch_request.execute(await asyncio.create_task(get_cached_token(GMAIL_TOKEN_ID))))
            except BatchError as err:
                return {'history_records': [], 'last_history_id': '', 'error': err}

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


def get_first_of_next_month(date):
    year, month = date.year, date.month
    if month == 12:
        month = 0
        year += 1
    return datetime.date(year, month, 1)


async def run_full_sync(resource, dbcon):
    dbcursor = dbcon.cursor()
    _now = datetime.datetime.now()
    app_info = get_app_info(dbcon)
    last_synced_date = app_info.last_synced_date  # int(internal_date format)
    date_of_oldest_email = app_info.date_of_oldest_email  # int(internal_date format)
    last_time_synced = app_info.last_time_synced  # float(datetime.timestamp format)

    if last_synced_date and (last_synced_date != date_of_oldest_email):
        full_sync_in_progress = True
    else:
        full_sync_in_progress = False
    synced_in_last_7_days = False
    if last_time_synced:
        last_time_synced = datetime.datetime.fromtimestamp(last_time_synced)
        if _now.date() - last_time_synced.date() <= datetime.timedelta(days=7):
            synced_in_last_7_days = True

    if (full_sync_in_progress and not synced_in_last_7_days and last_time_synced) or \
            (not full_sync_in_progress and not synced_in_last_7_days):
        # Start full sync from the beginning >>>
        LOG.warning(">>> FULL SYNC FROM THE BEGINNING >>>")
        app_info.last_synced_date = None
        app_info.update(dbcon)
        last_synced_date = None
        # Add one day because Gmail-API will ignore the last day.
        to_date = _now + datetime.timedelta(days=1)
        from_date = to_date - datetime.timedelta(days=30)
    elif synced_in_last_7_days and last_synced_date == date_of_oldest_email:
        # No need for full sync in this case, return >>>
        LOG.warning(">>> NO NEED FOR SYNCING >>>")
        return
    else:
        # Resume full sync >>>
        LOG.warning(">>> RESUMING FULL SYNC >>>")
        # NOTICE: Internal date is in UTC, make sure you use utcfromtimestamp
        from_date = datetime.datetime.utcfromtimestamp(idate_dtime(last_synced_date))
        to_date = from_date + datetime.timedelta(days=7)

    LOG.warning(f">>> Entering the synchronization while loop: {from_date.timestamp()}"
                f", {to_date.timestamp()}")
    while True:
        LOG.warning(f"From - To: {from_date} - {to_date}")
        # oldest_date_in_stage is in internal_date format.
        oldest_date_in_stage = await asyncio.create_task(
            synchronize(resource, dbcursor, from_date, to_date))
        if oldest_date_in_stage is None:
            LOG.warning("Checking if older email messages exist...")
            internal_date = await asyncio.create_task(older_message_exists(resource, from_date))
            if internal_date is None:
                # Now we know that this last_synced_date represents the date of the oldest email
                app_info.date_of_oldest_email = last_synced_date
                app_info.update(dbcon)
                break
            else:
                LOG.warning("Older message found !")
                # NOTICE: Internal date is in UTC, make sure you use utcfromtimestamp
                to_date = datetime.datetime.utcfromtimestamp(idate_dtime(internal_date)) + datetime.timedelta(days=1)
                from_date = to_date - datetime.timedelta(days=30)
                continue
        else:
            last_synced_date = oldest_date_in_stage

        # Save full sync progress
        app_info.last_synced_date = last_synced_date
        app_info.update(dbcon)
        to_date = from_date
        from_date = to_date - datetime.timedelta(days=30)
    LOG.warning(">>> DONE WITH SYNCHRONIZATION >>>")
    # Full sync is done, update last_time_synced
    app_info.last_time_synced = _now.timestamp()
    app_info.update(dbcon)


async def synchronize(resource, db_cursor, from_date, to_date):
    query = f"after:{from_date.year}/{from_date.month}/{from_date.day} " \
            f"before:{to_date.year}/{to_date.month}/{to_date.day}"

    msg_list = []
    token = ''
    while token != 'END':
        http = resource.users().messages().list(
            userId='me', maxResults=100, q=query, pageToken=token
        )

        p1 = time.perf_counter()
        async with aiohttp.ClientSession() as session:
            response, err_flag = await asyncio.create_task(send_request(session.get, http))
            if err_flag is False:
                response_data = json.loads(response)
            else:
                response_data = response
        p2 = time.perf_counter()
        LOG.info(f"<Sync Stage> List of emails fetched in: {p2 - p1} seconds.")
        if err_flag:
            LOG.error(f"Error data: {response_data}. Reporting an error...")
            return

        token = response_data.get('nextPageToken', 'END')
        msg_list.extend(response_data.get('messages', []))

    if len(msg_list) == 0:
        return None

    messages = []
    uri = 'https://gmail.googleapis.com/gmail/v1/users/me/messages/{0}?format=' \
          'metadata&metadataHeaders=To&metadataHeaders=From&metadataHeaders=Subject&alt=json'
    method = 'GET'
    essential_headers = {'accept': 'application/json', 'accept-encoding': 'gzip, deflate',
                         'user-agent': '(gzip)', 'x-goog-api-client': 'gdcl/1.12.8 gl-python/3.8.5'}
    b1 = time.perf_counter()
    batched = 0
    while batched < len(msg_list):
        batch = BatchApiRequest()
        for idx in range(batched, min(len(msg_list), batched + batch.MAX_BATCH_LIMIT)):
            resource_uri = uri.format(msg_list[idx]['id'])
            http_request = OptimizedHttpRequest(resource_uri, method, essential_headers, None)
            batch.add(http_request)
        batched += len(batch)
        try:
            fetched_msgs = await asyncio.create_task(batch.execute(http.headers['authorization']))
            messages.extend(fetched_msgs)
        except BatchError as err:
            LOG.error(f"Error occurred in batch request: {err}")
            return
    b2 = time.perf_counter()
    #LOG.info(f"Fetched {len(msg_list)} messages in batches of 100 in {p2 - p1} seconds.")

    p1 = time.perf_counter()
    for idx, msg in enumerate(messages):
        email_message = EmailMessage()
        email_message.message_id = int(msg.get('id'), 16)
        email_message.thread_id = int(msg.get('threadId'), 16)
        email_message.history_id = int(msg.get('historyId'))
        email_message.snippet = html_unescape(msg.get('snippet'))
        # Serialize label ids.
        email_message.label_ids = ','.join(msg.get('labelIds'))
        email_message.internal_date = int(msg.get('internalDate'))
        internal_timestamp = idate_dtime(msg.get('internalDate'))
        email_message.date = datetime.datetime.fromtimestamp(internal_timestamp).strftime('%b %d')
        for field in msg.get('payload').get('headers'):
            field_name = field.get('name').lower()
            if field_name == 'from':
                email_message.field_from = field.get('value').split('<')[0]
            elif field_name == 'to':
                email_message.field_to = field.get('value').split('<')[0].split('@')[0]
            elif field_name == 'subject':
                email_message.subject = field.get('value') or '(no subject)'
        messages[idx] = email_message
    p2 = time.perf_counter()

    # Internal date is in UTC, so we have to convert these to UTC as well before deleting rows
    # from the database, otherwise we will fail because of UNIQUE constraint when inserting.
    from_ts = datetime.datetime(
        from_date.year, from_date.month, from_date.day, tzinfo=datetime.timezone.utc).timestamp()
    to_ts = datetime.datetime(
        to_date.year, to_date.month, to_date.day, tzinfo=datetime.timezone.utc).timestamp()

    # Delete all messages between from_date and to_date.
    d1 = time.perf_counter()
    db_cursor.execute(
        'delete from Message where internal_date between {} and {};'.format(
            dtime_idate(from_ts), dtime_idate(to_ts)
        )
    )
    d2 = time.perf_counter()

    # debug_shit = [(m.message_id, m.thread_id, m.history_id, m.field_to, m.field_from, m.subject,
    #     m.snippet, m.internal_date, m.label_ids) for m in messages]
    # LOG.warning(f">>>>>>>>>>>>>>>>>>> DEBUG SHIT >>>>>>>>>>>>>>>>>> {debug_shit}")
    # Insert fresh messages created in the span of from_date to to_date.
    i1 = time.perf_counter()
    db_cursor.executemany('insert into message values(?,?,?,?,?,?,?,?,?)',
        ((m.message_id, m.thread_id, m.history_id, m.field_to, m.field_from, m.subject,
        m.snippet, m.internal_date, m.label_ids) for m in messages)
    )
    i2 = time.perf_counter()

    # At this point all messages in range of from_date to to_date have been synchronized.
    # Return the oldest email date. It should be the last one in the list, but let's better check.
    # TODO: Remove the loop once you are sure that oldest email date is at the end of the list.
    LOG.warning(f"Timings(batching, parsing, deletion, insertion): {b2-b1}, {p2-p1}, {d2-d1}, {i2-i1}")
    return messages[-1].internal_date


async def older_message_exists(resource, date):
    query = f"before:{date.year}/{date.month}/{date.day}"
    # Trying to fetch only 1 message, for minimal performance hit.
    http = resource.users().messages().list(userId='me', maxResults=1, q=query)
    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.get, http))
        if err_flag is False:
            response_data = json.loads(response)
        else:
            response_data = response
    if err_flag:
        LOG.error(f"Error data: {response_data}. Reporting an error...")
        return

    msgs_list = response_data.get('messages')
    if msgs_list is None:
        return None

    message_id = msgs_list[0].get('id')
    http = resource.users().messages().get(userId='me', id=message_id, format='minimal')
    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.get, http))
        if err_flag is False:
            response_data = json.loads(response)
        else:
            response_data = response
    if err_flag:
        LOG.error(f"Error data: {response_data}. Reporting an error...")
        return None

    internal_date = response_data.get('internalDate')
    if internal_date is None:
        return None
    return int(internal_date)


async def run_short_sync(resource, db, start_history_id, max_results,
                     types=['labelAdded', 'labelRemoved', 'messageAdded', 'messageDeleted']):
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
            return

        LOG.debug(f"RESPONSE DATA: {response_data}")
        all_history_records.extend(response_data.get('history', []))
        token = response_data.get('nextPageToken', '')
        if len(token) == 0:
            last_history_id = response_data.get('historyId')
            LOG.debug(f"LATEST HISTORY ID: {last_history_id}")
            LOG.debug(f"NUMBER OF HISTORY RECORDS: {len(all_history_records)}")
            break

        # Increase the amount of history-records to be fetched, but limit it to 100(each costs 2 quota)
        max_results = min(100, max_results + max_results)
        http = resource.users().history().list(
            userId='me', maxResults=max_results, startHistoryId=start_history_id,
            historyTypes=types, pageToken=token)

    # Now we have all history records in all_history_records
    # And we have the latest historyId in last_history_id

    history_records = {}
    for hrecord in all_history_records:
        new_parse_history_record(hrecord, history_records)

    messages = []
    uri = 'https://gmail.googleapis.com/gmail/v1/users/me/messages/{0}?format=' \
          'metadata&metadataHeaders=To&metadataHeaders=From&metadataHeaders=Subject&alt=json'
    method = 'GET'
    essential_headers = {'accept': 'application/json', 'accept-encoding': 'gzip, deflate',
                         'user-agent': '(gzip)', 'x-goog-api-client': 'gdcl/1.12.8 gl-python/3.8.5'}
    to_fetch_batch = BatchApiRequest()
    # Fetch what needs to be fetched
    for mid, hrecord in history_records.items():
        if hrecord.has_type(new_HistoryRecord.MESSAGE_ADDED):
            resource_uri = uri.format(mid)
            http_request = OptimizedHttpRequest(resource_uri, method, essential_headers, None)
            to_fetch_batch.add(http_request)
            if len(to_fetch_batch) < 100:
                continue
            try:
                fetched_msgs = await asyncio.create_task(
                    to_fetch_batch.execute(http.headres['authorization']))
                messages.extend(fetched_msgs)
            except BatchError as err:
                LOG.error(f"Error occurred in batch request: {err}")
                return
    if len(to_fetch_batch) > 0:
        try:
            fetched_msgs = await asyncio.create_task(
                to_fetch_batch.execute(http.headres['authorization']))
            for msg in fetched_msgs:
                history_records[msg.get('id')]
        except BatchError as err:
            LOG.error(f"Error occurred in batch request: {err}")
            return

    # TODO: I should separate all the changes into 3 parts:
    #  1.) Messages to delete(DELETE query)
    #  2.) Messages to add(INSERT INTO query)
    #  3.) Messages to modify (SELECT query and UPDATE query)
    to_delete = []
    to_add = []
    to_update = []
    for hrec in
