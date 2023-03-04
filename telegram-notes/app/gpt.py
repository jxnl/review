from typing import List
from dotenv import load_dotenv

load_dotenv()

import os
import openai

from loguru import logger

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

    # Process response
    logger.info(f"Got response from GPT-3: {response}")
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
    You are a world class life coach presented with notes from your clients journal. 
    You job is to help them explore their thoughts and feelings by suggesting them expand on their notes.
    The notes are just for the day, don't suggest topics that are unrelated to the day or too general.

    Response and try 1-2 thoughtful questions help the client expand their writing.
    When writing questions use bullet points to make it easier to read.
    Do not write too much as it is very expensive. Be concise. 
    To help them expand say something like 'Consider writing more about...' or 'What else happened?'
    If they start asking you to my questions suggest they focus on their own thoughts and feelings.
    """.strip()

    logger.info(f"generating follow up for {len(notes)} notes")

    # only take the last 50 notes to avoid GPT-3 running out of memory
    notes = notes[-50:]

    messages = [{"role": "system", "content": system}] + [
        {
            "role": "user" if n.is_user else "assistant",
            "content": n.msg,
        }
        for n in notes
    ]

    logger.info(f"messages: {messages}")

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
