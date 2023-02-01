import datetime
from dotenv import load_dotenv

load_dotenv()

import pymysql.cursors
import os
import gpt

from logging import getLogger

logger = getLogger(__name__)


connection = pymysql.connect(
    host=os.getenv("HOST"),
    user=os.getenv("USERNAME"),
    passwd=os.getenv("PASSWORD"),
    db=os.getenv("DATABASE"),
    ssl={"ca": os.getenv("PLANETSCALE_SSL_CERT_PATH")},
)

table_schems = """
CREATE TABLE `notes` (
	`id` int NOT NULL AUTO_INCREMENT,
	`created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP(),
	`telegram_user_id` bigint,
	`msg` text NOT NULL,
	`processed_msg` text,
	PRIMARY KEY (`id`)
) ENGINE InnoDB,

CREATE TABLE `summaries` (
	`id` int NOT NULL AUTO_INCREMENT,
	`telegram_user_id` bigint NOT NULL,
	`summary` text NOT NULL,
	`date` date NOT NULL,
	PRIMARY KEY (`id`)
) ENGINE InnoDB,
  """


def make_summary(telegram_user_id, date=None):

    if date is None:
        date = "DATE(NOW())"
    else:
        date = f"'{date}'"

    with connection.cursor() as cursor:
        sql = f"""
        SELECT 
            id, msg
        FROM 
            notes 
        WHERE 
            telegram_user_id = {telegram_user_id}
            AND DATE(created_at) = {date}
        """
        cursor.execute(sql)
        notes_objs = cursor.fetchall()
        ids = [note[0] for note in notes_objs]
        msgs = [note[1] for note in notes_objs]
    summary = gpt.generate_summary(msgs)
    return summary, ids


def save_summary(telegram_user_id, summary, ids):
    # check if there is already a summary for this user on this day
    with connection.cursor() as cursor:
        sql = """
        SELECT 
            id
        FROM 
            summaries 
        WHERE 
            telegram_user_id = %s 
            AND date = DATE(NOW())
        """
        cursor.execute(sql, (telegram_user_id))
        summary_id = cursor.fetchone()  # returns a tuple or None if there is no summary

        logger.info(
            f"summary_id: {summary_id} found for {telegram_user_id} on {datetime.date.today()}"
        )

        if summary_id is not None:
            # sanitize input
            summary_id = int(summary_id[0])

            sql = "UPDATE summaries SET summary=%s WHERE id=%s"
            cursor.execute(sql, (summary, summary_id))
            logger.info(
                f"Updated summary for {telegram_user_id} on {datetime.date.today()}"
            )
        else:
            # create new summary
            sql = "INSERT INTO summaries (telegram_user_id, summary, date) VALUES (%s, %s, DATE(NOW()))"
            cursor.execute(sql, (telegram_user_id, summary))
            logger.info(
                f"Created new summary for {telegram_user_id} on {datetime.date.today()}"
            )
            summary_id = cursor.lastrowid

        # update notes summary_id with the new summary
        sql = "UPDATE notes SET summary_id=%s WHERE id IN %s"
        cursor.execute(sql, (summary_id, tuple(ids)))
        connection.commit()
    return summary_id, ids


def save_note(telegram_user_id, from_message_id, message_text, processed_msg=None):
    """
    Save into table `notes` with schema:

        CREATE TABLE notes (
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            telegram_user_id INT NOT NULL,
            message_id INT NOT NULL,
            msg TEXT NOT NULL,
            processed_msg TEXT NULL
        );
    """

    # sanitize input
    telegram_user_id = int(telegram_user_id)
    from_message_id = int(from_message_id)
    message_text = str(message_text)
    processed_msg = str(processed_msg) if processed_msg else None

    # check if message_id already exsts
    with connection.cursor() as cursor:
        sql = "SELECT id FROM notes WHERE telegram_user_id=%s AND message_id=%s"
        cursor.execute(sql, (telegram_user_id, from_message_id))
        note_id = cursor.fetchone()

        # if it does not exist then save it
        if note_id:
            logger.info(f"Message {note_id[0]} already exists in database")
        else:
            sql = "INSERT INTO notes (telegram_user_id, message_id, msg, processed_msg) VALUES (%s, %s, %s, %s)"
            cursor.execute(
                sql, (telegram_user_id, from_message_id, message_text, processed_msg)
            )
            connection.commit()
            logger.info(f"Saved message {from_message_id} to database")
            note_id = cursor.lastrowid

    logger.info(f"Saved note {note_id} to database")
    return note_id


def delete_note(telegram_user_id, message_id):
    """
    Delete a note if it exists and was created by telegram_user_id
    """

    # sanitize input
    telegram_user_id = int(telegram_user_id)
    message_id = int(message_id)

    with connection.cursor() as cursor:
        sql = "DELETE FROM notes WHERE telegram_user_id=%s AND id=%s"

        try:
            cursor.execute(sql, (telegram_user_id, message_id))
            connection.commit()
        except MySQLdb.Error as e:
            logger.error("Error deleting message from database: {}".format(e))
            return None

    logger.info(f"Deleted message {message_id} from database")
    return message_id
