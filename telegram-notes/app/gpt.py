from typing import List
from dotenv import load_dotenv

load_dotenv()

import os
import openai
import logging

logger = logging.getLogger(__name__)

openai.api_key = os.environ["OPENAI_API_KEY"]


def generate(messages):
    gpt3_session = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=100,
        temperature=0.5,
    )

    # Generate a response to the user-provided message
    response = gpt3_session.choices[0].message.content.strip()  # type: ignore

    # Process response
    logger.info(f"Got response from GPT-3: {response}")
    return response


def generate_summary(notes: List[str]) -> str:
    system = """
    You are an AI assistant being presented with a list of notes the I've written down throughout the day. 
    Not all notes are related. Take those notes and generate a summary as a title. 
    Respond only with the summary not in quotes.""".strip()

    content = "\n".join([f"- {n}" for n in notes])

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": content},
    ]
    return generate(messages)


def generate_followup(notes: List[str]) -> str:
    system = """
    You are a world class life coach. 
    You are presented with notes from your clients journal. 
    Response and try 1-2 thoughtful questions help the client explore their thoughts.
    Do not be to percriptive, let the client lead the conversation.
    """.strip()

    if len(notes) == 1:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": notes[0]},
        ]
        return generate(messages)

    *rst, fst = [f"- {n}" for n in notes]
    rst = "\n".join(rst)

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": rst},
        {"role": "assistant", "content": "I'm listening..., what else happened?"},
        {"role": "user", "content": fst},
    ]

    return generate(messages)


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
