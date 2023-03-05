from typing import List
from dotenv import load_dotenv

load_dotenv()

import os
import openai

openai.api_key = os.environ["OPENAI_API_KEY"]


def generate(messages, max_tokens=100, temperature=0.5):
    gpt3_session = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    # Generate a response to the user-provided message
    response = gpt3_session.choices[0].message.content.strip()  # type: ignore
    return response


def generate_summary(notes: List[str]) -> str:
    system = """
    Writer being presented with a list of notes the throughout the day. 
    Take those notes and generate title for the journal entry.
    Respond only with the the title of the notes. Dont have stuff like 'summary: ..'""".strip()

    content = "\n".join([f"- {n.msg}" for n in notes if n.is_user])

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": content},
    ]
    return generate(messages, max_tokens=100, temperature=1)


def generate_followup(notes: List[str]) -> str:
    system = """
    You are a world class life coach bot named 'Orate' designed by @jxnlco.

    The conversation you have will be used to generate a diary entry / journal for the user.
    Your job is to help them explore their thoughts and feelings by suggesting them expand on their notes.
    The notes are just for the day, don't suggest topics that are unrelated to the day or too general.

    * Response and perhaps ask a thoughtful question to help the client expand their writing.
    * Limit the use of the mirroring technique as it can be annoying.
    * To help them expand say something like 'Consider talking more about...' or 'What else happened?'
    * If they start asking you to many unrelated questions suggest they focus on their own thoughts and feelings.
    * If they start deviating from journal like conversation, suggest they visit ChatGPT (chat.openai.com) for general converastins and their goal is to help you journal.
    * Only respond with 2-3 sentences and wait for a response, if you want to respond more, ask the client if they want you to expand on your response.
    * Instead of asking how they can be an assistant, ask them hows their day been so far.
    """.strip()

    # only take the last 50 notes to avoid GPT-3 running out of memory
    notes = notes[-50:]

    messages = [{"role": "system", "content": system}] + [
        {
            "role": "user" if n.is_user else "assistant",
            "content": n.msg,
        }
        for n in notes
    ]

    return generate(messages, max_tokens=500, temperature=0.3)


if __name__ == "__main__":
    notes = [
        "I had a great day today",
        "Went ice skating with my friends",
        "Thinking about my ice diving certification",
        "Stressed out about work",
        "I should work out more often to deal with the stress",
    ]
    print("Summary:")
    print(generate_summary(notes))
    print()
    print("Followup:")
    print(generate_followup(notes))
    print()
    print("Followup only one:")
    print(generate_followup(notes[:1]))
