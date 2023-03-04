from dotenv import load_dotenv

load_dotenv()

import os
import db

import flask
import telebot
import openai

openai.api_key = os.environ["OPENAI_API_KEY"]

from logging import getLogger

logger = getLogger(__name__)

app = flask.Flask(__name__)
bot = telebot.TeleBot(os.environ["TELEGRAM_BOT_TOKEN"], threaded=False)

ME = 5072074832
TRANSCRIPTION_URL = os.environ["TRANSCRIPTION_URL"]


@app.route("/")
def hello():
    return {"status": "ok"}


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


@app.route("/reminder", methods=["GET"])
def reminder():
    bot.send_message(os.environ["CHAT_ID"], "Any updates?")
    return {"status": "ok"}


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


# Handle '/delete_memo'
@bot.message_handler(commands=["delete_memo"], content_types=["text"])
def delete_message(message):
    user_id = message.from_user.id
    message_id = message.text.split(" ")[1]
    message_id = db.delete_note(telegram_user_id=user_id, message_id=message_id)

    if message_id:
        bot.reply_to(message, f"Deleted message {message_id} from database")
        return

    bot.reply_to(message, f"Message not found or not owned by user")


@bot.message_handler(commands=["summary"])
def send_summary(message):
    user_id = message.from_user.id
    date = message.text.split(" ")[1]

    try:
        summary_str, _, ids = db.make_summary(user_id, date)
        summary_id, ids = db.save_summary(user_id, summary_str, ids, date)
        logger.info(f"Saved summary {summary_id} to database for notes {ids}")
        bot.reply_to(message, summary_str)
    except Exception as e:
        logger.error(e)
        bot.reply_to(message, f"Error creating summary {e}")


def handle_message(message, message_text):
    user_id = message.from_user.id
    message_id = message.message_id

    message_id = db.save_note(
        telegram_user_id=user_id, from_message_id=message_id, message_text=message_text
    )
    try:
        summary_str, followup_str, ids = db.make_summary(user_id)
        _, ids = db.save_summary(user_id, summary_str, ids)
        bot.reply_to(message, followup_str)
    except Exception as e:
        logger.error(e)
        bot.reply_to(message, f"Error creating summary {e}")


@bot.message_handler(func=lambda message: True, content_types=["text"])
def handle_text(message):
    handle_message(message, message.text)


@bot.message_handler(content_types=["voice"])
def handle_voice(message):
    import requests

    file_id = message.voice.file_id
    logger.info(f"Received voice message with file_id: {file_id}")

    transcription = requests.get(TRANSCRIPTION_URL, params={"file_id": file_id})

    if transcription.status_code == 200:
        transcription = transcription.json()
        logger.info("Transcription successful {transcription}")
        bot.reply_to(message, transcription["text"])
        handle_message(message, transcription["text"])
    else:
        logger.error(f"Transcription failed {transcription}")
        bot.reply_to(message, "Transcription failed")


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    from loguru import logger

    polling = False

    logger.info("Starting bot")
    bot.remove_webhook()

    if polling:
        bot.infinity_polling()
    else:
        bot.set_webhook(url=os.environ["WEBHOOK_URL"])
        logger.info("Set webhook")
