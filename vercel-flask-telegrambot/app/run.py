from dotenv import load_dotenv

load_dotenv()

import os
import db
import collections

import flask
import telebot
from logging import getLogger

logger = getLogger(__name__)


app = flask.Flask(__name__)

bot = telebot.TeleBot(os.environ["TELEGRAM_BOT_TOKEN"], threaded=False)


@app.route("/")
def read_root():
    return {"status": "ok", "bot": "active"}


@app.route("/memos")
def return_memos():
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
    notes = collections.defaultdict(list)
    summaries = dict()
    note_tuples = db.fetch_notes()

    for day, summary, note_str in note_tuples:
        # format date to YYYY-MM-DD and collect into notes
        day = day.strftime("%Y-%m-%d")
        notes[day].append(note_str)
        summaries[day] = summary

    return {
        "memos": [{"date": k, "notes": v, "summary": summaries[day]} for (k, v) in notes.items()]
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
        ("Hi there, I am EchoBot.\n" "I am here to echo your kind words back to you."),
    )
    logger.info("Welcome message sent")


@bot.message_handler(commands=["save_memo"], content_types=["text"])
def save_message(message):
    user_id = message.from_user.id
    user_msg = message.text
    message_id = db.save_note(telegram_user_id=user_id, message_text=user_msg)
    bot.reply_to(message, f"Saved message {message_id} to database")


@bot.message_handler(commands=["delete_memo"], content_types=["text"])
def delete_message(message):
    user_id = message.from_user.id
    message_id = message.text.split(" ")[1]
    message_id = db.delete_note(telegram_user_id=user_id, message_id=message_id)

    if message_id:
        bot.reply_to(message, f"Deleted message {message_id} from database")
        return 

    bot.reply_to(message, f"Message not found or not owned by user")


if __name__ == "__main__":
    from loguru import logger

    logger.info("Starting bot")
    bot.remove_webhook()
    bot.set_webhook(url="https://learning-jxnl.vercel.app/webhook")
    # bot.infinity_polling()
    logger.info("Set webhook")
