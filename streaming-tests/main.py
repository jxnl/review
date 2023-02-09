from dataclasses import dataclass
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from youtube import extract_video_id, transcribe_youtube
from text_helpers import stream_summaries_from_text

import asyncio

app = FastAPI()


@dataclass
class SummaryPayload:
    url: str
    batch_size: int = 3000
    stream: int = True


@app.post("/stream_summary")
async def stream_summary(req: SummaryPayload) -> StreamingResponse:
    video_id = extract_video_id(req.url)
    text = transcribe_youtube(video_id)

    # this is the generator that yields the summaries
    generator = await stream_summaries_from_text(
        complete_batch=text, batch_size=req.batch_size
    )

    if req.stream:
        return StreamingResponse(generator, media_type="text/plain")
    else:
        acc = ""
        async for chunk in generator:
            acc += chunk
        return {"summary": acc}
