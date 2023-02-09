from dataclasses import dataclass
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from youtube import extract_video_id, transcribe_youtube
from text_helpers import stream_summaries_from_text
from logging import getLogger


import modal

stub = modal.Stub("summary")

image = modal.Image.debian_slim().pip_install(
    ["youtube-transcript-api", "openai", "fastapi"]
)

logger = getLogger(__name__)


@dataclass
class SummaryPayload:
    url: str
    batch_size: Optional[int] = 3000
    openai_api_key: Optional[str] = None
    engine: Optional[str] = "text-davinci-003"


@stub.webhook(method="POST", image=image, keep_warm=True)
async def youtube(req: SummaryPayload) -> StreamingResponse:
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
    generator = stream_summaries_from_text(
        complete_batch=text,
        batch_size=req.batch_size,
        openai_api_key=req.openai_api_key,
        engine=req.engine,
    )
    logger.info(f"Streaming summary for {video_id}...")
    return StreamingResponse(generator, media_type="text/plain")
