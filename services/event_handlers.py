from channels.event_channels import EmailEventChannel, ContactEventChannel, \
    ProcessEventChannel
from services.event import IPC_SHUTDOWN
from services.calls import fetch_messages, fetch_email, send_email, fetch_contacts, \
    add_contact, remove_contact, trash_email, untrash_email, delete_email, edit_contact, \
    short_sync

import asyncio
import multiprocessing
import contextlib


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
        if topic == 'page_request':
            func = fetch_messages
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

        if func is None:
            LOG.warning(f'Invalid topic, event_channel, topic, payload: {api_event.event_channel}, {api_event.topic}, {api_event.payload}')

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
                LOG.info("Received IPC_SHUTDOWN. Shutting down...")
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
