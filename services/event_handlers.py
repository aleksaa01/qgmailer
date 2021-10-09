from channels.event_channels import EmailEventChannel, ContactEventChannel, \
    ProcessEventChannel
from services.event import APIEvent, IPC_SHUTDOWN, NOTIFICATION_ID
from services.calls import get_emails_from_db, fetch_email, send_email, fetch_contacts, \
    add_contact, remove_contact, trash_email, untrash_email, delete_email, edit_contact, \
    short_sync, modify_labels, get_labels_diff
from services.db_calls import get_labels
from services.offline_calls import offline_trash_email, offline_untrash_email, offline_delete_email, \
    offline_modify_labels, offline_get_emails_from_db, offline_get_contacts_from_db
from services.api_calls import api_trash_email, api_untrash_email, api_delete_email, api_modify_labels

import asyncio
import multiprocessing
import json


LOG = multiprocessing.get_logger()


def create_api_task(con, con_list, func, *args, **kwargs):
    if len(con_list) == 0:
        con_list.append(con.acquire())

    resource = con_list.pop()
    return asyncio.create_task(func(resource, *args, **kwargs)), resource


class EventHandler:
    def __init__(self, gmail_con, people_con, gm_con_list, pe_con_list):
        self.gmail = gmail_con
        self.people = people_con
        self.gmail_cl = gm_con_list
        self.people_cl = pe_con_list

        self.tasks = []
        # hash map of: task -> (api_event, resource, connection_list)
        self.task_map = {}

        self.shutdown = False

    async def handle_event(self, api_event):
        if self.shutdown is True:
            raise OSError("Can't handle events after shutdown signal.")

        event_channel = api_event.event_channel
        if event_channel == EmailEventChannel:
            await self.handle_email_events(api_event)
        elif event_channel == ContactEventChannel:
            await self.handle_contact_events(api_event)
        elif event_channel == ProcessEventChannel:
            await self.handle_proc_events(api_event)

    async def handle_email_events(self, api_event):
        topic = api_event.topic
        func = None
        if topic == 'email_list_request':
            func = get_emails_from_db
        elif topic == 'labels_request':
            func = self._handle_labels_request
        elif topic == 'email_request':
            func = fetch_email
        elif topic == 'send_email':
            func = send_email
        elif topic == 'trash_email':
            func = trash_email
        elif topic == 'restore_email':
            func = untrash_email
        elif topic == 'delete_email':
            func = delete_email
        elif topic == 'short_sync':
            func = short_sync
        elif topic == 'modify_labels':
            func = modify_labels

        if func is None:
            LOG.warning(f'Invalid topic, event_channel, topic, payload: {api_event.event_channel}, {api_event.topic}, {api_event.payload}')
            return

        api_task, resource = create_api_task(self.gmail, self.gmail_cl, func, **api_event.payload)
        self.tasks.append(api_task)
        self.task_map[api_task] = (resource, api_event, self.gmail_cl)

    async def handle_contact_events(self, api_event):
        topic = api_event.topic
        func = None
        if topic == 'page_request':
            func = fetch_contacts
        elif topic == 'add_contact':
            func = add_contact
        elif topic == 'remove_contact':
            func = remove_contact
        elif topic == 'edit_contact':
            func = edit_contact

        if func is None:
            LOG.warning(f'Invalid topic, event_channel, topic, payload: {api_event.event_channel}, {api_event.topic}, {api_event.payload}')

        api_task, resource = create_api_task(self.people, self.people_cl, func, **api_event.payload)
        self.tasks.append(api_task)
        self.task_map[api_task] = (resource, api_event, self.people_cl)

    async def handle_proc_events(self, api_event):
        topic = api_event.topic
        flag = api_event.payload['flag']
        if topic == 'commands':
            if flag == IPC_SHUTDOWN:
                LOG.warning("Received IPC_SHUTDOWN. Shutting down...")
                self.shutdown = True

    def completed_tasks(self):
        tasks_removed = 0
        for idx, task in enumerate(self.tasks[:]):
            if task.done():
                resource, api_event, connection_list = self.task_map.pop(task)
                api_event.payload = task.result()
                self.tasks.pop(idx - tasks_removed)
                tasks_removed += 1
                connection_list.append(resource)
                LOG.info(f"Length of gmail and people connection list: {len(self.gmail_cl)}, {len(self.people_cl)}")
                yield api_event

    async def _handle_labels_request(self, resource):
        labels_task = asyncio.create_task(get_labels())

        api_event = APIEvent(NOTIFICATION_ID, EmailEventChannel, 'labels_sync')
        api_task, resource = create_api_task(self.gmail, self.gmail_cl, get_labels_diff)
        self.tasks.append(api_task)
        self.task_map[api_task] = (resource, api_event, self.gmail_cl)

        labels = await labels_task

        return {'labels': {'all': labels}}


class OfflineEventHandler:

    def __init__(self):
        self.tasks = []
        self.task_map = {}
        self.shutdown = False

    async def handle_event(self, api_event):
        if self.shutdown is True:
            raise OSError("Can't handle events after shutdown signal.")

        event_channel = api_event.event_channel
        if event_channel == EmailEventChannel:
            await self.handle_email_events(api_event)
        elif event_channel == ContactEventChannel:
            await self.handle_contact_events(api_event)
        elif event_channel == ProcessEventChannel:
            await self.handle_proc_events(api_event)

    async def handle_email_events(self, api_event):
        topic = api_event.topic
        func = None
        if topic == 'email_list_request':
            func = offline_get_emails_from_db
        elif topic == 'labels_request':
            func = self._handle_labels_request
        elif topic == 'trash_email':
            func = offline_trash_email
        elif topic == 'restore_email':
            func = offline_untrash_email
        elif topic == 'delete_email':
            func = offline_delete_email
        elif topic == 'modify_labels':
            func = offline_modify_labels

        if func is None:
            LOG.warning(
                f'Invalid topic, event_channel, topic, payload: {api_event.event_channel}, {api_event.topic}, {api_event.payload}')
            return

        api_task = asyncio.create_task(func(**api_event.payload))
        self.tasks.append(api_task)
        self.task_map[api_task] = api_event

    async def handle_contact_events(self, api_event):
        topic = api_event.topic
        func = None
        if topic == 'page_request':
            func = offline_get_contacts_from_db

        if func is None:
            LOG.warning(
                f'Invalid topic, event_channel, topic, payload: {api_event.event_channel}, {api_event.topic}, {api_event.payload}')
            return

        api_task = asyncio.create_task(func(**api_event.payload))
        self.tasks.append(api_task)
        self.task_map[api_task] = api_event

    async def handle_proc_events(self, api_event):
        topic = api_event.topic
        flag = api_event.payload['flag']
        if topic == 'commands':
            if flag == IPC_SHUTDOWN:
                LOG.warning("Received IPC_SHUTDOWN. Shutting down...")
                self.shutdown = True

    def completed_tasks(self):
        tasks_removed = 0
        for idx, task in enumerate(self.tasks[:]):
            if task.done():
                api_event = self.task_map.pop(task)
                api_event.payload = task.result()
                self.tasks.pop(idx - tasks_removed)
                tasks_removed += 1
                yield api_event

    async def _handle_labels_request(self):
        labels_task = asyncio.create_task(get_labels())
        labels = await labels_task

        return {'labels': {'all': labels}}


async def apply_offline_changes(gmail_resource, db, change_list):
    # TODO: Currently we can't have cascading implications, and thus one change failing won't
    #  actually have any unexpected consequences.
    # 0 - id, 1 - api_type, 2 - action_type, 3 - payload
    for change in change_list:
        try:
            change_id = change[0]
            action_type = change[2]
            payload = change[3]
            LOG.info(f"Change >>> {change_id}, {change[1]}, {action_type}")
            if action_type == 'trash_email':
                message_id = json.loads(payload).get('message_id')
                await api_trash_email(gmail_resource, message_id)
            elif action_type == 'untrash_email':
                message_id = json.loads(payload).get('message_id')
                await api_untrash_email(gmail_resource, message_id)
            elif action_type == 'delete_email':
                message_id = json.loads(payload)
                await api_delete_email(gmail_resource, message_id)
            elif action_type == 'modify_labels':
                data = json.loads(payload)
                await api_modify_labels(
                    gmail_resource, data.get('message_id'), data.get('to_add'), data.get('to_remove')
                )
            else:
                raise TypeError(f"Unsupported action type: {action_type}")

            # Change has been applied, delete it from the database.
            await db.execute('DELETE FROM ChangeList WHERE id = ?', (change_id, ))
            await db.commit()
        except Exception as err:
            LOG.error(f"Unable to apply change({change}): {err}")
