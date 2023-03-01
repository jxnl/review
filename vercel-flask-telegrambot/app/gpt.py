from dotenv import load_dotenv

load_dotenv()

import os
import openai
import logging

logger = logging.getLogger(__name__)

openai.api_key = os.environ["OPENAI_API_KEY"]


def generate_summary(notes):
    # join all notes into a single string as a set of bullet points
    notes = ["* " + note for note in notes]
    notes = "\n".join(notes)

    gpt3_session = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": """You are an AI assistant being presented with a list of notes the I've written down throughout the day. Not all notes are related. Take those notes and generate an interesting title for the day. Respond only with the title not in quotes.""",
            },
            {"role": "user", "content": f"Notes:\n{notes}"},
        ],
    )

    # Generate a response to the user-provided message
    response = gpt3_session.choices[0].message.content.strip()  # type: ignore

    # Process response
    logger.info(f"Got response from GPT-3: {response}")
    return response


if __name__ == "__main__":
    notes = [
        "I had a great day today",
        "Went ice skating with my friends",
    ]
    print(generate_summary(notes))
