from dataclasses import dataclass
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from youtube import extract_video_id, transcribe_youtube
from text_helpers import stream_summaries_from_text


app = FastAPI()


@dataclass
class SummaryPayload:
    url: str
    batch_size: int = 3000
    stream: int = True
    openai_api_key: str = None
    engine: str = "text-davinci-003"


@app.post("/stream_summary")
async def stream_summary(req: SummaryPayload) -> StreamingResponse:
    video_id = extract_video_id(req.url)
    text = transcribe_youtube(video_id)

    if len(text) == 0:
        if req.stream:
            return StreamingResponse(
                status_code=404, content="Video transcript not found on youtube"
            )
        else:
            return {"summary": "Video transcript not found on youtube"}

    # this is the generator that yields the summaries
    generator = stream_summaries_from_text(
        complete_batch=text,
        batch_size=req.batch_size,
        openai_api_key=req.openai_api_key,
        engine=req.engine,
    )

    if req.stream:
        return StreamingResponse(generator, media_type="text/plain")
    else:
        acc = ""
        async for chunk in generator:
            acc += chunk
        return {"summary": acc}
