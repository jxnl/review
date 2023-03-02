from dotenv import load_dotenv

load_dotenv()

import os
import db
import io

import flask
import telebot
import openai

openai.api_key = os.environ["OPENAI_API_KEY"]

from logging import getLogger

logger = getLogger(__name__)

app = flask.Flask(__name__)
bot = telebot.TeleBot(os.environ["TELEGRAM_BOT_TOKEN"], threaded=False)

ME = 5072074832


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
        summary_str, ids = db.make_summary(user_id, date)
        summary_id, ids = db.save_summary(user_id, summary_str, ids, date)
        bot.reply_to(message, f"Saved summary {summary_id} to database for notes {ids}")
        bot.reply_to(message, summary_str)
    except Exception as e:
        logger.error(e)
        bot.reply_to(message, f"Error creating summary {e}")


@bot.message_handler(func=lambda message: True, content_types=["text"])
def save_message(message):
    user_id = message.from_user.id
    message_id = message.message_id
    user_msg = message.text
    message_id = db.save_note(
        telegram_user_id=user_id, from_message_id=message_id, message_text=user_msg
    )
    bot.reply_to(message, f"Saved message {message_id} to database.")
    try:
        summary_str, ids = db.make_summary(user_id)
        summary_id, ids = db.save_summary(user_id, summary_str, ids)
        bot.reply_to(message, f"Saved summary {summary_id} to database for notes {ids}")
    except Exception as e:
        logger.error(e)
        bot.reply_to(message, f"Error creating summary {e}")


if __name__ == "__main__":
    from loguru import logger

    polling = False

    logger.info("Starting bot")
    bot.remove_webhook()

    if polling:
        bot.infinity_polling()
    else:
        bot.set_webhook(url="https://telebot-nine-lemon.vercel.app/webhook")
        logger.info("Set webhook")
