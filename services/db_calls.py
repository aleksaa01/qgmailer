from persistence.db import acquire_connection, release_connection
from googleapis.gmail.labels import GMAIL_LABEL_TRASH


async def get_emails(label_id, limit, offset):
    db = await acquire_connection()
    if label_id != GMAIL_LABEL_TRASH:
        data = await db.execute_fetchall(
            'SELECT * FROM Message '
            'WHERE label_ids LIKE "%{}%" '
            'AND label_ids NOT LIKE "%TRASH%" '
            'ORDER BY internal_date DESC '
            'LIMIT {} OFFSET {}'.format(label_id, limit, offset)
        )
    else:
        data = await db.execute_fetchall(
            'SELECT * FROM Message '
            'WHERE label_ids LIKE "%{}%" '
            'ORDER BY internal_date DESC '
            'LIMIT {} OFFSET {}'.format(label_id, limit, offset)
        )

    await release_connection(db)
    return data


async def get_labels():
    db = await acquire_connection()
    data = await db.execute_fetchall('SELECT * FROM Label')
    await release_connection(db)
    return data


async def get_contacts():
    db = await acquire_connection()
    data = await db.execute_fetchall('SELECT * FROM Contact')
    await release_connection(db)
    return data
