from dotenv import load_dotenv

load_dotenv()

import os

import wiki_bot
import telebot


bot = telebot.TeleBot(os.environ["TELEGRAM_BOT_TOKEN"], threaded=False)


# Handle '/start' and '/help'
@bot.message_handler(commands=["help", "start"])
def send_welcome(message):
    bot.reply_to(
        message,
        """
        Welcome to the demo bot

        /wiki <query> - Use a langchain search bot to look through Wikipedia for an answer to your question
        """,
    )


@bot.message_handler(commands=["wiki"])
def wiki(message):
    query = message.text.split(" ", 1)[1]
    response = wiki_bot.react.run(query)
    bot.reply_to(message, response)


bot.infinity_polling()
