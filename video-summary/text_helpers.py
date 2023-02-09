import asyncio
import openai
import logging

logger = logging.getLogger(__name__)


def chunk_texts(text, chunk_size=5000):
    import re

    sentences = re.split(r' *[\.\?!][\'"\)\]]* *', text)
    block = ""
    for sentence in sentences:
        block += sentence
        if len(block) > chunk_size:
            yield block
            block = ""
    yield block


async def summarize(text, openai_api_key=None, engine="text-davinci-003"):
    logger.info("Summarizing text with OpenAI")
    if openai_api_key is not None:
        openai.api_key = openai_api_key
    # Create a completion generator
    response = await openai.Completion.acreate(
        engine=engine,
        prompt=f"Summarize this video transcript, do not mention the existance of a transcribe just start with the facts: \n\n {text} Begin summary: \n\n",
        stream=True,
        max_tokens=1000,
        temperature=0.2,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.6,
    )

    async def gen():
        async for chunk in response:
            yield chunk["choices"][0]["text"]

    return gen()


async def stream_summaries_from_text(complete_batch, batch_size=3000, **kwargs):
    """
    Stream summaries from a text. This is a generator that yields
    the summaries as they are generated.

    Parameters
    ----------
    text: str
        The text to summarize
    batch_size: int
        The number of characters to send to OpenAI at a time."""
    chunks = chunk_texts(complete_batch, chunk_size=batch_size)
    logger.info(f"Summarizing {chunks} chunks.")
    completion = await asyncio.gather(*[summarize(chunk, **kwargs) for chunk in chunks])
    for resp in completion:
        async for cr in resp:
            yield cr
