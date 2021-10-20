from googleapis.gmail.gparser import extract_body
from googleapis.gmail.labels import *
from googleapis.gmail.history import parse_history_record, HistoryRecord
from googleapis.gmail.messages import async_parse_all_email_messages, parse_email_message
from logs.loggers import default_logger
from persistence.db import get_app_info, acquire_connection, release_connection
from services.db_calls import get_labels, get_emails, get_contacts
from services.api_calls import TOKEN_CACHE, send_request, BatchApiRequest, OptimizedHttpRequest, \
    BatchError, api_trash_email, api_untrash_email, api_delete_email, api_modify_labels, \
    api_total_messages_with_label_id
from services.utils import email_message_to_dict, internal_date_to_timestamp, int_to_hex, \
    hex_to_int, timestamp_to_internal_date, db_message_to_dict, db_message_to_email_message

from html import unescape as html_unescape

import asyncio
import aiohttp
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

FULL_SYNC_IN_PROGRESS = False


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


async def send_email(resource, email_msg):
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
        return {'label_id': GMAIL_LABEL_SENT, 'email': {}, 'error': response_data}

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
        return {'email': {}, 'error': response_data}

    message = parse_email_message(response_data)

    db = await acquire_connection()
    await db.execute(
        'INSERT INTO Message VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (message.message_id, message.thread_id, message.history_id, message.field_to,
         message.field_from, message.subject, message.snippet, message.internal_date,
         message.label_ids)
    )
    await db.commit()
    await release_connection(db)

    parsed_email = email_message_to_dict(message)

    return {'email': parsed_email}


async def fetch_contacts(resource, fields=None):
    # page_token = page_token or TOKEN_CACHE.get('contacts', '')
    # if page_token == 'END':
    #     LOG.info(f'All contacts have been already fetched.')
    #     return {'contacts': []}

    if fields is None:
        fields = 'names,emailAddresses'

    unparsed_contacts = []
    total_contacts = 0
    page_token = ''
    while True:
        http = resource.people().connections().list(
            resourceName='people/me', personFields=fields,
            pageSize=90, pageToken=page_token
        )
        async with aiohttp.ClientSession() as session:
            response, err_flag = await asyncio.create_task(send_request(session.get, http))
            if err_flag is False:
                response_data = json.loads(response)
            else:
                response_data = response
        if err_flag:
            LOG.error(f"Failed to fetch contacts. Error: {response_data}")
            return {'contacts': [], 'total_contacts': 0, 'error': response_data}

        page_token = response_data.get('nextPageToken')
        total_contacts = response_data.get('totalItems')
        unparsed_contacts.extend(response_data.get('connections', []))
        if not page_token:
            break

    LOG.debug(F"TOTAL NUMBER OF ITEMS IN connections.list is: {total_contacts}")
    contacts = []
    # givenName = first name; familyName = last name; displayName = maybe both;
    for con in unparsed_contacts:
        name = ''
        email = ''
        names = con.get('names', [])
        emails = con.get('emailAddresses', [])
        if names:
            name = names[0]['displayName']
        if emails:
            email = emails[0]['value']

        contacts.append(
            {'name': name, 'email': email, 'etag': con.get('etag'),
             'resourceName': con.get('resourceName')}
        )

    db = await acquire_connection()
    # We fetched all possible contacts, now delete everything from db and insert all fetched contacts.
    await db.execute('DELETE FROM Contact;')
    await db.executemany(
        'INSERT INTO Contact VALUES(?, ?, ?, ?)',
        [(c.get('resourceName'), c.get('etag'), c.get('name'), c.get('email')) for c in contacts]
    )
    await db.commit()
    await release_connection(db)

    return {'contacts': contacts, 'total_contacts': len(contacts)}


async def fetch_email(resource, message_id):
    # TODO: Check the database before you query the API.
    db = await acquire_connection()
    data = await db.execute_fetchall(
        'SELECT * FROM Email WHERE message_pk=? LIMIT 1', (message_id,)
    )
    if data:
        await release_connection(db)
        body, attachments = extract_body(data[0][1])
        return {'body': body, 'attachments': attachments}

    http = resource.users().messages().get(id=int_to_hex(message_id), userId='me', format='raw')

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

    await db.execute('INSERT OR REPLACE INTO Email VALUES(?, ?)', (message_id, response_data['raw']))
    await db.commit()
    await release_connection(db)
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
    response_data, err_flag = await api_trash_email(resource, email.get('message_id'))

    if err_flag:
        LOG.error(f"Failed to send email to trash. Parameters: {email}, {from_lbl_id}, {to_lbl_id}."
                  f"Error data: {response_data}.")
        return {'email': email, 'from_lbl_id': from_lbl_id, 'to_remove': [], 'error': response_data}

    to_remove = email.get('label_ids').split(',')
    label_ids = ','.join(response_data['labelIds'])
    email['label_ids'] = label_ids

    db = await acquire_connection()
    await db.execute(
        'UPDATE Message SET label_ids = ? WHERE message_id = ?', (label_ids, email.get('message_id'))
    )
    await db.commit()
    await release_connection(db)

    return {'email': email, 'from_lbl_id': from_lbl_id, 'to_remove': to_remove}


async def untrash_email(resource, email):
    response_data, err_flag = await api_untrash_email(resource, email.get('message_id'))

    if err_flag:
        LOG.error(f"Failed to restore email from trash. Parameters: {email}. Error data: {response_data}")
        return {'email': email, 'to_add': [], 'error': response_data}

    to_add = response_data['labelIds']
    email['label_ids'] = ','.join(to_add)

    db = await acquire_connection()
    await db.execute(
        'UPDATE Message SET label_ids = ? WHERE message_id = ?',
        (email.get('label_ids'), email.get('message_id'))
    )
    await db.commit()
    await release_connection(db)

    return {'email': email, 'to_add': to_add}


async def delete_email(resource, label_id, message_id):
    response_data, err_flag = await api_delete_email(resource, message_id)

    if err_flag:
        LOG.error(f"Failed to delete an email. Parameters: {label_id}, {message_id}. Error data: {response_data}")
        return {'label_id': label_id, 'error': response_data}

    db = await acquire_connection()
    await db.execute('DELETE FROM Message WHERE message_id = ?', (message_id,))
    await db.commit()
    await release_connection(db)

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

    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.patch, http, data=http.body))
        if err_flag is False:
            response_data = json.loads(response)
        else:
            response_data = response

    if err_flag:
        LOG.error(f"Failed to edit a contact. Parameters: {name}, {email}, {contact}. Error data: {response_data}")
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


async def total_messages_with_label_id(resource, label_id):
    response_data, err_flag = await api_total_messages_with_label_id(resource, label_id)

    if err_flag:
        LOG.error(
            f"Failed to get total messages in label-id: {label_id}. Error data: {response_data}.")
        return {'label_id': label_id, 'num_messages': 0, 'error': response_data}

    total_messages = response_data['messagesTotal']
    return {'label_id': label_id, 'num_messages': total_messages}


async def modify_labels(resource, message_id, all_labels, to_add, to_remove):
    response_data, err_flag = await api_modify_labels(resource, message_id, to_add, to_remove)

    if err_flag:
        LOG.error(f"Failed to modify labels. Parameters: {message_id}, {all_labels}, {to_add}, {to_remove}."
                  f"Error: {response_data}")

    all_labels = all_labels.split(',')
    for lbl in to_remove:
        all_labels.remove(lbl)
    for lbl in to_add:
        all_labels.append(lbl)
    all_labels = ','.join(all_labels)

    db = await acquire_connection()
    await db.execute(
        'UPDATE Message SET label_ids = ? WHERE message_id = ?', (all_labels, message_id)
    )
    await db.commit()
    await release_connection(db)

    LOG.debug("Labels modified successfully.")
    return {}


def get_first_of_next_month(date):
    year, month = date.year, date.month
    if month == 12:
        month = 0
        year += 1
    return datetime.date(year, month, 1)


async def full_sync(resource):
    global FULL_SYNC_IN_PROGRESS
    # Set full sync to True immediately, because short sync might run before we are able
    # to set it again.
    FULL_SYNC_IN_PROGRESS = True

    _now = datetime.datetime.now()
    app_info = await get_app_info()
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
        LOG.debug("STARTING FULL SYNC.")
        app_info.last_synced_date = None
        await app_info.update()
        last_synced_date = None
        # Add one day because Gmail-API will ignore the last day.
        to_date = _now + datetime.timedelta(days=1)
        from_date = to_date - datetime.timedelta(days=30)
    elif synced_in_last_7_days and last_synced_date == date_of_oldest_email:
        # No need for full sync in this case, return >>>
        LOG.debug("FULL SYNC NOT NEEDED.")
        FULL_SYNC_IN_PROGRESS = False
        return True
    else:
        # Resume full sync >>>
        LOG.debug("RESUMING FULL SYNC.")
        # NOTICE: Internal date is in UTC, make sure you use utcfromtimestamp
        from_date = datetime.datetime.utcfromtimestamp(internal_date_to_timestamp(last_synced_date))
        to_date = from_date + datetime.timedelta(days=7)

    latest_history_id = app_info.latest_history_id or 0
    while True:
        LOG.debug(f"From - To: {from_date} - {to_date}")
        try:
            # oldest_date_in_stage is in internal_date format.
            oldest_date_in_stage, latest_history_id_in_stage = await sync_stage(resource, from_date, to_date)
        except Exception as err:
            LOG.error(f"sync_stage failed, aborting full sync. Error: {err}")
            # TODO: If full sync returns False, that means it failed to execute.
            #  Next thing we should do is send a shutdown signal and close the event loop.
            #  Or try to restart the application ?
            return False

        if latest_history_id_in_stage:
            latest_history_id = max(latest_history_id, latest_history_id_in_stage)

        if oldest_date_in_stage is None:
            LOG.debug("Checking if older email messages exist...")
            internal_date = await asyncio.create_task(older_message_exists(resource, from_date))
            if internal_date is None:
                # Now we know that this last_synced_date represents the date of the oldest email
                app_info.date_of_oldest_email = last_synced_date
                await app_info.update()
                break
            else:
                LOG.debug("Older message found !")
                # NOTICE: Internal date is in UTC, make sure you use utcfromtimestamp
                to_date = datetime.datetime.utcfromtimestamp(
                    internal_date_to_timestamp(internal_date)
                ) + datetime.timedelta(days=1)
                from_date = to_date - datetime.timedelta(days=30)
                continue
        else:
            last_synced_date = oldest_date_in_stage

        # Save full sync progress
        app_info.last_synced_date = last_synced_date
        app_info.latest_history_id = latest_history_id
        await app_info.update()
        to_date = from_date
        from_date = to_date - datetime.timedelta(days=30)
    LOG.debug("FULL SYNCHRONIZATION DONE.")
    # Full sync is done, update last_time_synced
    app_info.last_time_synced = _now.timestamp()
    await app_info.update()

    FULL_SYNC_IN_PROGRESS = False
    return True


async def sync_stage(resource, from_date, to_date):
    query = f"after:{from_date.year}/{from_date.month}/{from_date.day} " \
            f"before:{to_date.year}/{to_date.month}/{to_date.day}"

    msg_list = []
    token = ''
    while token != 'END':
        http = resource.users().messages().list(
            userId='me', maxResults=100, q=query,
            pageToken=token, includeSpamTrash=True
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
        return None, None

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
    await asyncio.create_task(async_parse_all_email_messages(messages))
    p2 = time.perf_counter()

    # Internal date is in UTC, so we have to convert these to UTC as well before deleting rows
    # from the database, otherwise we will fail because of UNIQUE constraint when inserting.
    # TODO: We are still hitting the integrity error, looks like Gmail API calculates this stuff in a
    #  different way. Figure out what's wrong, but in the mean time "insert or replace into" query
    #  should be enough to get the job done.
    from_ts = datetime.datetime(
        from_date.year, from_date.month, from_date.day, tzinfo=datetime.timezone.utc).timestamp()
    to_ts = datetime.datetime(
        to_date.year, to_date.month, to_date.day, tzinfo=datetime.timezone.utc).timestamp()

    # Delete all messages between from_date and to_date.
    d1 = time.perf_counter()
    db = await acquire_connection()
    await db.execute(
        'delete from Message where internal_date between ? and ?;',
        (timestamp_to_internal_date(from_ts), timestamp_to_internal_date(to_ts))
    )
    d2 = time.perf_counter()

    # Insert fresh messages created in the span of from_date to to_date.
    i1 = time.perf_counter()
    await db.executemany('insert or replace into Message values(?,?,?,?,?,?,?,?,?);',
        ((m.message_id, m.thread_id, m.history_id, m.field_to, m.field_from, m.subject,
        m.snippet, m.internal_date, m.label_ids) for m in messages)
    )
    await db.commit()
    await release_connection(db)
    i2 = time.perf_counter()

    # At this point all messages in range of from_date to to_date have been synchronized.
    # Return the oldest email date(it's the last one in the list).
    LOG.info("Length, batching, parsing, deletion, insertion): "
                f"{len(messages)}, {b2-b1}, {p2-p1}, {d2-d1}, {i2-i1}")

    latest_history_id = max(messages, key=lambda m: m.history_id).history_id
    oldest_date = messages[-1].internal_date
    return oldest_date, latest_history_id


async def older_message_exists(resource, date):
    query = f"before:{date.year}/{date.month}/{date.day}"
    # Fetch only 1 message, for minimal performance hit.
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


async def short_sync(resource, max_results=10,
                     types=['labelAdded', 'labelRemoved', 'messageAdded', 'messageDeleted']):

    LOG.debug("SHORT SYNC STARTED.")

    if FULL_SYNC_IN_PROGRESS:
        LOG.debug("Stopping SHORT SYNC, because FULL SYNC is in progress....")
        return {'history_records': {}}

    app_info = await get_app_info()
    start_history_id = app_info.latest_history_id

    http = resource.users().history().list(
        userId='me', maxResults=max_results, startHistoryId=start_history_id, historyTypes=types)

    unparsed_history_records = []
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
            return {'history_records': {}, 'error': response_data}

        LOG.debug(f"RESPONSE DATA: {response_data}")
        unparsed_history_records.extend(response_data.get('history', []))
        token = response_data.get('nextPageToken', '')
        if len(token) == 0:
            last_history_id = int(response_data.get('historyId'))
            LOG.debug(f"LATEST HISTORY ID: {last_history_id}")
            LOG.debug(f"NUMBER OF HISTORY RECORDS: {len(unparsed_history_records)}")
            break

        # Increase the amount of history-records to be fetched, but limit it to 100(each costs 2 quota)
        max_results = min(100, max_results + max_results)
        http = resource.users().history().list(
            userId='me', maxResults=max_results, startHistoryId=start_history_id,
            historyTypes=types, pageToken=token)

    # Now we have all history records in unparsed_history_records
    # And we have the latest historyId in last_history_id

    history_records = {}
    for hrecord in unparsed_history_records:
        parse_history_record(hrecord, history_records)

    uri = 'https://gmail.googleapis.com/gmail/v1/users/me/messages/{0}?format=' \
          'metadata&metadataHeaders=To&metadataHeaders=From&metadataHeaders=Subject&alt=json'
    method = 'GET'
    essential_headers = {'accept': 'application/json', 'accept-encoding': 'gzip, deflate',
                         'user-agent': '(gzip)', 'x-goog-api-client': 'gdcl/1.12.8 gl-python/3.8.5'}
    to_fetch_batch = BatchApiRequest()
    # Fetch what needs to be fetched
    for idx, (db_mid, hrecord) in enumerate(history_records.items()):
        if hrecord.has_type(HistoryRecord.MESSAGE_ADDED):
            resource_uri = uri.format(int_to_hex(db_mid))
            http_request = OptimizedHttpRequest(resource_uri, method, essential_headers, None)
            to_fetch_batch.add(http_request)
            if len(to_fetch_batch) < 100 and idx < len(history_records) - 1:
                # Continue if batch is not full, unless we are at last history record
                continue
            try:
                fetched_msgs = await asyncio.create_task(
                    to_fetch_batch.execute(http.headers['authorization']))
                for msg in fetched_msgs:
                    email_message = parse_email_message(msg)
                    history_records[email_message.message_id].message = email_message
            except BatchError as err:
                LOG.error(f"Error occurred in batch request: {err}")
                return {'history_records': {}, 'error': err}

    # Update stages:
    # 1.) Messages to delete(DELETE query)
    # 2.) Messages to add(INSERT INTO query)
    # 3.) Messages to modify (SELECT query and UPDATE query)
    to_delete = []
    to_add = []
    to_update = {}
    for mid, hrec in history_records.items():
        if hrec.has_type(HistoryRecord.MESSAGE_DELETED):
            to_delete.append((mid,))
        elif hrec.has_type(HistoryRecord.MESSAGE_ADDED):
            m = hrec.message
            to_add.append((m.message_id, m.thread_id, m.history_id, m.field_to, m.field_from,
                           m.subject, m.snippet, m.internal_date, m.label_ids))
        # These should only handle modified messages, NOT ADDED AND ALSO MODIFIED.
        elif hrec.labels_modified():
            to_update[mid] = (hrec.labels_added, hrec.labels_removed)
        else:
            assert False

    db = await acquire_connection()

    queryset = await db.execute_fetchall('SELECT * FROM Message WHERE message_id IN ({})'.format(
        ','.join('?' for _ in range(len(to_delete)))),
        [mid for mid, in to_delete]  # This is how you destructure a tuple of length 1
    )
    # Update history records
    for msg_data in queryset:
        message = db_message_to_email_message(msg_data)
        history_records[message.message_id].message = message

    await db.executemany('DELETE FROM Message WHERE message_id = ?;', to_delete)

    await db.executemany('INSERT OR IGNORE INTO Message VALUES(?,?,?,?,?,?,?,?,?);', to_add)

    queryset = await db.execute_fetchall('SELECT * FROM Message WHERE message_id IN ({})'.format(
        ','.join('?' for _ in range(len(to_update)))),
        [mid for mid in to_update.keys()]
    )

    for idx, msg_data in enumerate(queryset):
        message = db_message_to_email_message(msg_data)
        history_records[message.message_id].message = message
        added, removed = to_update.get(message.message_id)
        label_ids = message.label_ids.split(',')
        for lid in removed:
            try:
                label_ids.remove(lid)
            except ValueError:
                pass
        for lid in added:
            label_ids.append(lid)
        # Update label_ids
        label_ids = ','.join(label_ids)
        message.label_ids = label_ids
        queryset[idx] = (label_ids, message.message_id)

    await db.executemany('UPDATE Message SET label_ids = ? WHERE message_id = ?', queryset)
    await db.commit()
    await release_connection(db)
    app_info = await get_app_info()
    app_info.last_time_synced = datetime.datetime.now().timestamp()
    app_info.latest_history_id = last_history_id
    await app_info.update()
    LOG.debug("SHORT SYNCHRONIZATION DONE.")

    return {'history_records': history_records}


async def fetch_labels(resource):
    http = resource.users().labels().list(userId='me')
    ###
    async with aiohttp.ClientSession() as session:
        response, err_flag = await asyncio.create_task(send_request(session.get, http))
        if err_flag is False:
            response_data = json.loads(response)
        else:
            response_data = response

    if err_flag:
        LOG.error(f"Error occurred while fetching list of label IDs. Error: {response_data}")
        return

    auth = http.headers['authorization']
    label_list = response_data['labels']
    labels = []
    batched = 0
    while batched < len(label_list):
        batch = BatchApiRequest()
        for idx in range(batched, min(len(label_list), batched + batch.MAX_BATCH_LIMIT)):
            # TODO: Rewrite this to use OptimizedHttpRequest
            http = resource.users().labels().get(userId='me', id=label_list[idx].get('id'))
            batch.add(http)

        batched += len(batch)
        try:
            fetched_lbls = await asyncio.create_task(batch.execute(auth))
            labels.extend(fetched_lbls)
        except BatchError as err:
            LOG.error(f"Label batch request failed. Error: {err}")
            return

    # Organize them in lists so they can be more easily comparable with data in the database,
    labels = [(l['id'], l['name'], l['type'], l.get('messageListVisibility'),
         l.get('labelListVisibility'), l['messagesTotal'], l.get('color', {}).get('textColor'),
         l.get('color', {}).get('backgroundColor')) for l in labels]

    return labels


async def get_labels_diff(resource):
    db_labels = await get_labels()
    fetched_labels = await fetch_labels(resource)

    labels_diff = {'added': [], 'modified': [], 'deleted': []}
    for fl in fetched_labels:
        lid = fl[0]
        found = False
        for idx, dl in enumerate(db_labels):
            if dl[0] == lid:
                found = True
                if fl != dl:
                    labels_diff['modified'].append(fl)
                break
        if not found:
            labels_diff['added'].append(fl)
        else:
            db_labels.pop(idx)

    for lbl in db_labels:
        labels_diff['deleted'].append(lbl)

    db = await acquire_connection()
    # Delete both deleted and modified Labels
    await db.executemany(
        'DELETE FROM Label WHERE label_id = ?',
        ((l[0],) for l in labels_diff['deleted'] + labels_diff['modified'])
    )
    # Insert both modified and added labels
    await db.executemany(
        'INSERT INTO Label VALUES(?, ?, ?, ?, ?, ?, ?, ?)',
        (l for l in labels_diff['added'] + labels_diff['modified'])
    )
    await db.commit()
    await release_connection(db)

    return {'labels': labels_diff}


async def get_emails_from_db(resource, label_id, limit, offset):
    t1 = time.perf_counter()
    data = await get_emails(label_id, limit, offset)
    t2 = time.perf_counter()
    emails = [0] * len(data)
    for idx, row in enumerate(data):
        emails[idx] = db_message_to_dict(row)
    t3 = time.perf_counter()

    return {'label_id': label_id, 'limit': limit, 'emails': emails, 'fully_synced': not FULL_SYNC_IN_PROGRESS}


async def get_contacts_from_db(resource):
    data = await get_contacts()
    contacts = [0] * len(data)
    for idx, row in enumerate(data):
        contact = {'resourceName': row[0], 'etag': row[1], 'name': row[2], 'email': row[3]}
        contacts[idx] = contact

    return {'contacts': contacts, 'total_contacts': len(contacts)}
