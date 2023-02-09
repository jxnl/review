from dataclasses import dataclass
from typing import Optional
from fastapi import FastAPI, Header
from fastapi.responses import StreamingResponse
from youtube import extract_video_id, transcribe_youtube
from text_helpers import stream_summaries_from_text
from logging import getLogger


import modal

stub = modal.Stub("summary")

image = modal.Image.debian_slim().pip_install(
    ["youtube-transcript-api", "openai", "fastapi", "sse-starlette"]
)

logger = getLogger(__name__)


@dataclass
class SummaryPayload:
    url: str


app = FastAPI()


@stub.webhook(method="POST", image=image, keep_warm=True)
@app.post("/youtube")
async def youtube(
    req: SummaryPayload, authorization: str = Header(None)
) -> StreamingResponse:
    if authorization is None or not authorization.startswith("Bearer "):
        return StreamingResponse(
            status_code=401, content="Authorization header is required"
        )
    bearer, token = authorization.split(" ")

    video_id = extract_video_id(req.url)
    logger.info(f"Received request for {video_id}")

    try:
        text = transcribe_youtube(video_id)
        head_text = text[:200]
        logger.info(f"Transcript for {video_id} is {head_text}...")
    except:
        return StreamingResponse(
            status_code=404, content="Video transcript not found on youtube"
        )

    if len(text) > 3000 * 10:
        return StreamingResponse(
            status_code=404,
            content="Video transcript is too long to summarize without your own OpenAI API key.",
        )

    # this is the generator that yields the summaries
    generator = stream_summaries_from_text(complete_batch=text, openai_api_key=token)
    logger.info(f"Streaming summary for {video_id}...")
    return StreamingResponse(generator, media_type="text/plain")


from sse_starlette import EventSourceResponse


@stub.webhook(method="POST", image=image, keep_warm=True)
@app.post("/youtube_sse")
async def youtube_sse(
    req: SummaryPayload, authorization: str = Header(None)
) -> StreamingResponse:
    if authorization is None or not authorization.startswith("Bearer "):
        return StreamingResponse(
            status_code=401, content="Authorization header is required"
        )
    bearer, token = authorization.split(" ")
    video_id = extract_video_id(req.url)
    logger.info(f"Received request for {video_id}")

    try:
        text = transcribe_youtube(video_id)
        head_text = text[:200]
        logger.info(f"Transcript for {video_id} is {head_text}...")
    except:
        return EventSourceResponse(
            status_code=404, content="Video transcript not found on youtube"
        )

    if len(text) > 3000 * 10:
        return EventSourceResponse(
            status_code=404,
            content="Video transcript is too long to summarize without your own OpenAI API key.",
        )

    # this is the generator that yields the summaries
    generator = stream_summaries_from_text(
        complete_batch=text,
        openai_api_key=token,
    )

    async def event_stream():
        async for summary in generator:
            yield {"data": summary}
        yield {"data": "[DONE]"}

    logger.info(f"Streaming summary for {video_id}...")
    return EventSourceResponse(event_stream(), media_type="text/plain")
