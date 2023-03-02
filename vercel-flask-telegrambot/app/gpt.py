from typing import List
from dotenv import load_dotenv

load_dotenv()

import os
import openai
import logging

logger = logging.getLogger(__name__)

openai.api_key = os.environ["OPENAI_API_KEY"]


def generate(notes, prompt: str):
    # join all notes into a single string as a set of bullet points
    notes = ["* " + note for note in notes]
    notes = "\n".join(notes)

    gpt3_session = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {"role": "user", "content": f"Notes:\n{notes}"},
        ],
        max_tokens=100,
        temperature=0.2,
    )

    # Generate a response to the user-provided message
    response = gpt3_session.choices[0].message.content.strip()  # type: ignore

    # Process response
    logger.info(f"Got response from GPT-3: {response}")
    return response


def generate_summary(notes: List[str]) -> str:
    prompt = "You are an AI assistant being presented with a list of notes the I've written down throughout the day. Not all notes are related. Take those notes and generate a summary as a title. Respond only with the summary not in quotes."
    return generate(notes, prompt)


def generate_followup(notes: List[str]) -> str:
    prompt = "You are an AI assistant being presented with a list of notes the I've written down throughout the day. Generate some thought provoking follow up questions, only use 2-3"
    return generate(notes, prompt)


if __name__ == "__main__":
    notes = [
        "I had a great day today",
        "Went ice skating with my friends",
    ]
    print(generate_summary(notes))
    print(generate_followup(notes))
