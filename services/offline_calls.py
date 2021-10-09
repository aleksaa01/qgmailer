from googleapis.gmail.labels import *
from persistence.db import acquire_connection, release_connection
from services.calls import get_emails_from_db, get_contacts_from_db

import json

# NOTICE !
# These function only mimic the behaviour of the API and record their changes in a list of changes.
# At this point I should really consider adding some test because functionality is now split into 2
# modes, one online one offline, and I might easily forget to update both if I change something, thus
# breaking one of them.


async def offline_get_emails_from_db(label_id, limit, offset):
    return await get_emails_from_db(None, label_id, limit, offset)


async def offline_get_contacts_from_db():
    return await get_contacts_from_db(None)


async def offline_trash_email(email, from_lbl_id, to_lbl_id):
    to_remove = email.get('label_ids').split(',')
    to_add = [GMAIL_LABEL_TRASH]
    new_label_ids = ','.join(to_add + to_remove)
    email['label_ids'] = new_label_ids
    db = await acquire_connection()
    await db.execute(
        'UPDATE Message SET label_ids = ? WHERE message_id = ?',
        (new_label_ids, email.get('message_id'))
    )
    await db.execute(
        'INSERT INTO ChangeList VALUES(?, ?, ?, ?)', (None, 'gmail', 'trash_email', json.dumps(email))
    )
    await db.commit()
    await release_connection(db)

    return {'email': email, 'from_lbl_id': from_lbl_id, 'to_remove': to_remove}


async def offline_untrash_email(email):
    label_ids = email.get('label_ids').split(',')
    label_ids.remove(GMAIL_LABEL_TRASH)
    to_add = label_ids
    label_ids = ','.join(label_ids)
    email['labelIds'] = label_ids

    db = await acquire_connection()
    await db.execute(
        'UPDATE Message SET label_ids = ? WHERE message_id = ?', (label_ids, email.get('message_id'))
    )
    await db.execute(
        'INSERT INTO ChangeList VALUES(?, ?, ?, ?)', (None, 'gmail', 'untrash_email', json.dumps(email))
    )
    await db.commit()
    await release_connection(db)

    return {'email': email, 'to_add': to_add}


async def offline_delete_email(label_id, message_id):
    db = await acquire_connection()
    await db.execute('DELETE FROM Message WHERE message_id = ?', (message_id,))
    await db.execute(
        'INSERT INTO ChangeList VALUES(?, ?, ?, ?)',
        (None, 'gmail', 'delete_email', json.dumps({'message_id': message_id}))
    )
    await db.commit()
    await release_connection(db)

    return {'label_id': label_id}


async def offline_modify_labels(message_id, all_labels, to_add, to_remove):
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
    serialized_change = json.dumps({'message_id': message_id, 'to_add': to_add, 'to_remove': to_remove})
    await db.execute(
        'INSERT INTO ChangeList VALUES(?, ?, ?, ?)', (None, 'gmail', 'modify_labels', serialized_change)
    )
    await db.commit()
    await release_connection(db)

    return {}
