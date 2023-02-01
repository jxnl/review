from dotenv import load_dotenv

load_dotenv()

import os
import openai
import logging

logger = logging.getLogger(__name__)

openai.api_key = os.environ["OPENAI_TOKEN"]


def generate_summary(notes):

    # join all notes into a single string as a set of bullet points
    notes = ["* " + note for note in notes]
    notes = "\n".join(notes)

    prompt = f"""
    You are an AI assistant being presented with a list of notes the I've written down throughout the day.
    Not all notes are related. Take those notes and generate an interesting title for the day.

    Notes:
    {notes}
    
    Title:
    """

    logger.info(f"Sending prompt to GPT-3: {prompt}")
    # Create a GPT-3 session
    gpt3_session = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0.8,
        max_tokens=1000,
        n=1,
    )

    # Generate a response to the user-provided message
    response = gpt3_session.choices[0].text.strip()  # type: ignore

    # Process response
    logger.info(f"Got response from GPT-3: {response}")
    return response
