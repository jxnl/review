from dotenv import load_dotenv

load_dotenv()

import os
import openai
import logging

logger = logging.getLogger(__name__)

openai.api_key = os.environ["OPENAI_TOKEN"]

def get_gpt_response(prompt):
    """
    Get a response from GPT-3
    """
    openai.api_key = os.environ["OPENAI_API_KEY"]


def generate_summary(note_objs):
    # Define the prompt that will be sent to GPT-3

    # join all notes into a single string as a set of bullet points
    notes = ["* " + note[0] for note in note_objs]
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
        max_tokens=2024,
        n=1,
    )

    # Generate a response to the user-provided message
    response = gpt3_session.choices[0].text  # type: ignore

    # Process response
    logger.info(f"Got response from GPT-3: {response}")
    return response
