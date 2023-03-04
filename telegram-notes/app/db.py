from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

import datetime
import pymysql.cursors

import os
import gpt

from loguru import logger


connection = pymysql.connect(
    host=os.getenv("PLANETSCALE_DB_HOST"),
    user=os.getenv("PLANETSCALE_DB_USERNAME"),
    passwd=os.getenv("PLANETSCALE_DB_PASSWORD"),
    db=os.getenv("PLANETSCALE_DB_DATABASE"),
    ssl={"ca": os.getenv("PLANETSCALE_SSL_CERT_PATH")},
)

table_schems = """
CREATE TABLE `notes` (
	`id` int NOT NULL AUTO_INCREMENT,
	`created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP(),
	`telegram_user_id` bigint,
	`msg` text NOT NULL,
    `is_user` boolean NOT NULL DEFAULT 1,
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


@dataclass
class Note:
    id: int
    msg: str
    is_user: bool


def make_summary(telegram_user_id, date=None) -> tuple[str, str, list[int]]:
    if date is None:
        date = "DATE(NOW())"
    else:
        date = f"'{date}'"

    logger.info(f"Make summary and follow up for {telegram_user_id} on {date}")

    with connection.cursor() as cursor:
        sql = f"""
        SELECT 
            id, msg, is_user
        FROM 
            notes 
        WHERE 
            telegram_user_id = {telegram_user_id}
            AND DATE(created_at) = {date}
        ORDER BY 1
        """
        cursor.execute(sql)
        notes_objs = cursor.fetchall()
        notes = [Note(*note) for note in notes_objs]
    summary = gpt.generate_summary(notes)
    followup = gpt.generate_followup(notes)

    save_followup(telegram_user_id, followup)
    save_summary(telegram_user_id, summary, [n.id for n in notes])

    return followup


def save_followup(telegram_user_id, followup):
    followup = followup.replace("'", "\\'")
    logger.info(f"saving followup {telegram_user_id}: {followup}")
    with connection.cursor() as cursor:
        # save the followup note to the database
        sql = f"""
        INSERT INTO notes 
            (telegram_user_id, msg, is_user)
        VALUES
            ({telegram_user_id}, '{followup}', 0)
        """
        cursor.execute(sql)
        logger.info(f"Saved followup note for {telegram_user_id} ")


def save_summary(telegram_user_id, summary, ids, date=None):
    # check if there is already a summary for this user on this day

    # sanitize input
    summary = summary.replace("'", "\\'")
    if date is None:
        date = "DATE(NOW())"
    else:
        date = f"'{date}'"

    with connection.cursor() as cursor:
        sql = f"""
        SELECT 
            id
        FROM 
            summaries 
        WHERE 
            telegram_user_id = {telegram_user_id} 
            AND date = {date}
        """
        cursor.execute(sql)
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

    # check if message_id already exsts
    with connection.cursor() as cursor:
        sql = "SELECT id FROM notes WHERE telegram_user_id=%s AND message_id=%s"
        cursor.execute(sql, (telegram_user_id, from_message_id))
        note_id = cursor.fetchone()

        # if it does not exist then save it
        if note_id:
            logger.info(f"Message {note_id[0]} already exists in database")
        else:
            sql = "INSERT INTO notes (telegram_user_id, message_id, msg) VALUES (%s, %s, %s)"
            cursor.execute(sql, (telegram_user_id, from_message_id, message_text))
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
