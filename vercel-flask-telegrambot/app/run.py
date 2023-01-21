import flask
import telebot

app = flask.Flask(__name__)

bot = telebot.TeleBot("5833781579:AAG5TY68zJ05zH4GVTX-ay7_ddooX5ezhNA")


@app.route("/")
def read_root():
    return {"status": "ok", "bot": "active"}


# Process webhook calls
@app.route("/webhook", methods=["POST"])
def webhook():
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
    bot.reply_to(
        message,
        ("Hi there, I am EchoBot.\n" "I am here to echo your kind words back to you."),
    )


# Handle all other messages
@bot.message_handler(func=lambda message: True, content_types=["text"])
def echo_message(message):
    bot.reply_to(message, message.text)


bot.remove_webhook()
bot.set_webhook(url="https://learning-jxnl.vercel.app/webhook")
