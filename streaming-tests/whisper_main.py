from typing import List
from loguru import logger

import asyncio

inc = 1


async def whisper_task(transcript_queue):
    logger.info("whisper: starting whisper")
    for i in range(40):
        chunk = f"Transcription: {i}"
        logger.info(f"whisper: sleeping 1 sec to simulate slow stream : {chunk}")
        await asyncio.sleep(inc)
        transcript_queue.put_nowait(chunk)
    transcript_queue.put_nowait(None)


async def openai_request(chunks: List[str]):
    msg = "".join(chunks)
    logger.info("open ai request: starting request")
    await asyncio.sleep(1)

    # return the message in chunks of 100 characters
    for i in range(0, len(msg), 10):
        await asyncio.sleep(0.01)
        yield msg[i : i + 10]

    return


async def request_handler(transcript_queue, response_queue, chunk_size=10):
    chunks = []
    while True:
        chunk = await transcript_queue.get()

        # when chunk is None, the queue is closed
        if chunk is None:
            break

        chunks.append(chunk)
        if len(chunks) > chunk_size:
            max_chunk = max([c.split(" ")[-1] for c in chunks])
            logger.info(
                f"Batch collected from transcriptions queue with top chunk: {max_chunk}"
            )
            async for openai_chunk in openai_request(chunks):
                response_queue.put_nowait(openai_chunk)
            chunks = []

    # ensures the last chunk is sent
    async for openai_chunk in openai_request(chunks):
        response_queue.put_nowait(openai_chunk)

    # ensures the response queue is closed
    response_queue.put_nowait(None)
    return


# fastapi streaming
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

app = FastAPI()


class TranscriptionPayload:
    download_path: str
    stream: str = True
    whisper_model: str = "base"
    summary_model: str = "openai-davinci-003"
    char_size: int = 3000


async def stream_queue(queue):
    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        yield chunk


@app.post("/transcribe")
async def transcribe():
    logger.info("transcribe: starting transcribe")
    transcript_queue = asyncio.Queue()
    asyncio.ensure_future(whisper_task(transcript_queue))
    return StreamingResponse(stream_queue(transcript_queue), media_type="text/plain")


@app.post("/stream")
async def stream_summary() -> StreamingResponse:
    transcript_queue = asyncio.Queue()
    response_queue = asyncio.Queue()

    # Runs them in the background and returns the response queue to the caller immediately
    asyncio.ensure_future(
        asyncio.gather(
            whisper_task(transcript_queue),
            request_handler(transcript_queue, response_queue),
        )
    )

    return StreamingResponse(stream_queue(response_queue), media_type="text/plain")
