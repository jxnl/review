from dotenv import load_dotenv

load_dotenv()

import MySQLdb
import os

from logging import getLogger

logger = getLogger(__name__)

connection = MySQLdb.connect(
    host=os.getenv("HOST"),
    user=os.getenv("USERNAME"),
    passwd=os.getenv("PASSWORD"),
    db=os.getenv("DATABASE"),
    ssl_mode="VERIFY_IDENTITY",
    ssl={"ca": "/etc/ssl/cert.pem"},
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

def fetch_notes():
    """
    Fetches the notes from the database, and returns a list of tuples
    
    Returns:
        list: [(date, summary, note), (date, summary, note)]
    """
    with connection.cursor() as cursor:
        sql = """
        SELECT 
            DATE(created_at) as day,
            summary,
            msg as memo
        FROM 
            notes 
            JOIN summaries ON notes.telegram_user_id = summaries.telegram_user_id 
                AND DATE(notes.created_at) = summaries.date
        WHERE 
            notes.telegram_user_id = 5072074832 
        """
        cursor.execute(sql)
        notes_objs = cursor.fetchall()
    
    logger.info("Fetched {} notes from database".format(len(notes_objs)))
    return notes_objs


def save_note(telegram_user_id, message_text, processed_msg=None):
    """
    Save into table `notes` with schema:

        CREATE TABLE notes (
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            telegram_user_id INT NOT NULL,
            msg TEXT NOT NULL,
            processed_msg TEXT NULL
        );
    """

    # sanitize input
    telegram_user_id = int(telegram_user_id)
    message_text = str(message_text)
    processed_msg = str(processed_msg) if processed_msg else None

    with connection.cursor() as cursor:
        sql = "INSERT INTO notes (telegram_user_id, msg, processed_msg) VALUES (%s, %s, %s)"
        cursor.execute(sql, (telegram_user_id, message_text, processed_msg))
        connection.commit()

    message_id = cursor.lastrowid
    logger.info(f"Saved message {message_id} to database")
    return message_id


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