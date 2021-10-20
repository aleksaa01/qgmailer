from services.utils import int_to_hex

from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.feedparser import FeedParser
from email.generator import Generator
from urllib.parse import urlparse, urlunparse
from io import StringIO

from logs.loggers import default_logger

import asyncio
import aiohttp
import json
import uuid
import httplib2
import time
import urllib
import datetime

LOG = default_logger()

# This token cache includes tokens from api calls and creds that store bearer tokens
TOKEN_CACHE = {}
GMAIL_TOKEN_ID = 'g-creds'
PEOPLE_TOKEN_ID = 'p-creds'


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
    async with aiohttp.ClientSession() as session:
        response, err_flag = await send_request(session.post, url=url, data=post_data, headers=headers)

    if err_flag:
        raise Exception(f"Failed to refresh the token. Error: {response}")

    response_data = json.loads(response)
    credentials.token = response_data['access_token']
    credentials._refresh_token = response_data.get('refresh_token', credentials._refresh_token)
    credentials.expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=response_data.get('expires_in'))
    credentials._id_token = response_data.get('id_token')


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
        url = kwargs.pop('url')
        headers = kwargs.pop('headers')
        token_id = kwargs.get('token_id')

    backoff = 1
    while True:
        try:
            async with session_request_method(url=url, headers=headers, **kwargs) as response:
                status = response.status
                if 200 <= status < 300:
                    return await response.text(encoding='utf-8'), False
                # 429 - Too many requests
                elif status == 403 or status == 429:
                    LOG.warning(f"Rate limit exceeded, waiting {backoff} seconds.")
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    if backoff > 32:
                        return await response.text(encoding='utf-8'), True
                # 401 - Gmail | 410 - People
                elif status == 401 or status == 410:
                    LOG.warning(f"send_request: {status} error encountered. Refreshing the token...")
                    if http is not None:
                        await asyncio.create_task(validate_http(http, headers))
                    else:
                        token = await asyncio.create_task(get_cached_token(token_id))
                        headers['authorization'] = token
                else:
                    LOG.error(f"Unknown error in send_request, status: {status}")
                    return await response.text(encoding='utf-8'), True
        except aiohttp.ClientConnectionError as err:
            if backoff > 32:
                LOG.error("Failed to send a request, endpoint is unreachable and back-off is greater than 32 seconds."
                          f"Parameters(url, headers): {url}, {headers}")
                raise

            LOG.warning(f"Endpoint({url}) is unreachable, waiting {backoff} seconds.")
            await asyncio.sleep(backoff)
            backoff *= 2


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
        self._batch_uri = 'https://gmail.googleapis.com/batch/gmail/v1'
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

        for rid, request in enumerate(self.requests):
            msg_part = MIMENonMultipart("application", "http")
            msg_part["Content-Transfer-Encoding"] = "binary"
            msg_part["Content-ID"] = self._id_to_header(str(rid))

            body = await asyncio.create_task(self._serialize_request(request))
            msg_part.set_payload(body)
            message.attach(msg_part)

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
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url=self._batch_uri, data=body, headers=headers) as response:
                        status = response.status
                        if 200 <= status < 300:
                            content = await response.text(encoding='utf-8')
                        elif status == 403 or status == 429:
                            LOG.warning(f"Rate limit exceeded while sending the batch request"
                                        f"(403={status==403,}, 429={status==429}), waiting {backoff} seconds.")
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
                            LOG.error(f"Unhandled error in BatchApiRequest.execute. Error: {data}")
                            raise BatchError(f"{data}")
                p2 = time.perf_counter()
                LOG.info(f"Batch response fetched in : {p2 - p1} seconds.")
            except aiohttp.ClientConnectionError as err:
                if backoff > 32:
                    LOG.error("Failed to send the batch request. Batch endpoint is unreachable and "
                              "back-off is greater than 32 seconds.")
                    raise
                LOG.warning(f"Batch endpoint is unreachable, waiting {backoff} seconds.")
                await asyncio.sleep(backoff)
                backoff *= 2
            else:
                break

        await self.handle_response(response, content)
        if len(self.requests) > 0:
            LOG.warning(f"{len(self.requests)} tasks FAILED, calling execute again.")
            await self.execute()
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
                    LOG.error(f"BatchApiRequest: Unhandled error in one of the responses: {parsed_response}."
                              f"\n\tRequest uri, method, headers: {http_request.uri}, {http_request.method},"
                              f"{http_request.headers}")
                    continue
                failed_requests.append(http_request)
            else:
                self.completed_responses.append(parsed_response)

        self.requests = failed_requests
        if error_401:
            self.access_token = await asyncio.create_task(get_cached_token(GMAIL_TOKEN_ID))
        if error_403 or error_429:
            LOG.warning(f"One or more responses failed with rate limit exceeded(403={error_403}, 429={error_429}), "
                        f"waiting {self.backoff} seconds.")
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


async def api_trash_email(resource, message_id):
    # Response only contains: id, threadId, labelIds
    http = resource.users().messages().trash(
        userId='me', id=int_to_hex(message_id)
    )

    p1 = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.post, http, data=http.body))
        if err_flag is False:
            response_data = json.loads(response)
        else:
            response_data = response
    p2 = time.perf_counter()
    LOG.info(f"Email sent to trash in: {p2 - p1} seconds.")
    return response_data, err_flag


async def api_untrash_email(resource, message_id):
    http = resource.users().messages().untrash(
        userId='me', id=int_to_hex(message_id)
    )

    p1 = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.post, http, data=http.body))
        if err_flag is False:
            response_data = json.loads(response)
        else:
            response_data = response
    p2 = time.perf_counter()
    LOG.info(f"Email restored from trash in: {p2 - p1} seconds.")
    return response_data, err_flag


async def api_delete_email(resource, message_id):
    http = resource.users().messages().delete(userId='me', id=int_to_hex(message_id))

    p1 = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.delete, http, data=http.body))
        # If email was successfully deleted, response body will be emtpy
        response_data = response
    p2 = time.perf_counter()
    LOG.info(f"Email deleted in: {p2 - p1} seconds.")

    return response_data, err_flag


async def api_total_messages_with_label_id(resource, label_id):
    http = resource.users().labels().get(userId='me', id=label_id)
    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.get, http))
        response_data = json.loads(response)

    return response_data, err_flag


async def api_modify_labels(resource, message_id, to_add, to_remove):
    # TODO: This is currently only used for marking the email message as READ.
    #  As you can see it's not even reporting errors. So in the future it should send 2 lists.
    #  One specifying where to add the email, and second from where to remove it.
    body = {
        "removeLabelIds": list(to_remove),
        "addLabelIds": list(to_add)
    }
    http = resource.users().messages().modify(userId='me', id=int_to_hex(message_id), body=body)

    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.post, http, data=http.body))

    return response, err_flag
