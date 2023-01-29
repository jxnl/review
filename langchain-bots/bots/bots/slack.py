from dotenv import load_dotenv

load_dotenv()

import os

import wiki_bot
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler


# Install the Slack app and get xoxb- token in advance
app = App(token=os.environ["SLACK_BOT_TOKEN"])


@app.event("/wiki")
def squery(ack, say, command):
    ack()
    query = command["text"]
    response = wiki_bot.react.run(query)
    say(response)


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
