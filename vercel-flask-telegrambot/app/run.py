from dotenv import load_dotenv

load_dotenv()

import os
import db
import collections
import requests

import flask
import telebot
from logging import getLogger

logger = getLogger(__name__)


app = flask.Flask(__name__)

bot = telebot.TeleBot(os.environ["TELEGRAM_BOT_TOKEN"], threaded=False)

ME = 5072074832


@app.route("/")
def hello():
    return {"status": "ok"}


@app.route("/memos/<month>")
def return_memos(month:int):
    """
    Returns the number of notes saved in the data from the database for each telegram user

    Returns:
        dict: {
            "memos": [
                "date": "2020-01-01",
                "notes": [
                    "note1", "note2"
                ]
                "summary": None
            ]
        }
    """
    month = int(month)

    note_tuples = db.fetch_notes(month)

    notes = collections.defaultdict(list)
    summaries = dict()

    for day, summary, note_str in note_tuples:
        # format date to YYYY-MM-DD and collect into notes
        day = day.strftime("%Y-%m-%d")
        notes[day].append(note_str)
        summaries[day] = summary

    ordered_by_date = sorted(notes.items(), reverse=True)

    return {
        "memos": [
            {"date": day, "notes": notes, "summary": summaries[day]}
            for (day, notes) in ordered_by_date
        ]
    }


# Process webhook calls
@app.route("/webhook", methods=["POST"])
def webhook():
    logger.info("Webhook called")
    if flask.request.headers.get("content-type") == "application/json":
        json_string = flask.request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ""
    else:
        flask.abort(403)


# Handle '/start' and '/help'
@bot.message_handler(commands=["help", "start"])
def send_welcome(message):
    logger.info(f"Welcome message to {message.from_user.first_name}")
    bot.reply_to(
        message,
        """
        Welcome to the memo bot. 
        
        To save a message, use the command /memo followed by your message.
        To delete a message, use the command /delete_memo followed by the message id.
        """,
    )
    logger.info("Welcome message sent")


@bot.message_handler(commands=["delete_memo"], content_types=["text"])
def delete_message(message):
    user_id = message.from_user.id
    message_id = message.text.split(" ")[1]
    message_id = db.delete_note(telegram_user_id=user_id, message_id=message_id)

    if message_id:
        bot.reply_to(message, f"Deleted message {message_id} from database")
        return

    bot.reply_to(message, f"Message not found or not owned by user")


@bot.message_handler(func=lambda message: True, content_types=["text"])
def save_message(message):
    user_id = message.from_user.id
    message_id = message.message_id
    user_msg = message.text
    message_id = db.save_note(
        telegram_user_id=user_id, from_message_id=message_id, message_text=user_msg
    )
    bot.reply_to(
        message, f"Saved message {message_id} to database."
    )
    try:
        summary = db.make_summary(user_id)
        summary_id = db.save_summary(user_id, summary)
        bot.reply_to(message, f"Saved summary {summary_id} to database")
    except Exception as e:
        logger.error(e)
        bot.reply_to(message, f"Error creating summary {e}")


@bot.message_handler(content_types=["voice"])
def transcribe(message):
    file_id = message.voice.file_id
    logger.info(f"Received voice message with file_id: {file_id}")
    transcription = requests.get("https://jxnl--telegram-transcribe.modal.run/", params={"file_id": file_id})

    if transcription.status_code == 200:
        transcription = transcription.json()

        logger.info("Transcription successful {transcription}")

    bot.reply_to(message, transcription["text"])




if __name__ == "__main__":
    from loguru import logger

    polling = False

    logger.info("Starting bot")
    bot.remove_webhook()

    if polling:
        bot.infinity_polling()
    else:
        bot.set_webhook(url="https://learning-jxnl.vercel.app/webhook")
        logger.info("Set webhook")
