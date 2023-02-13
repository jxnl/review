import glob
import modal
import os
import json

from dataclasses import dataclass, field


def download_whisper():
    import whisper

    whisper.load_model("tiny")
    whisper.load_model("large")
    return


img = (
    modal.Image.debian_slim()
    .pip_install("ffmpeg-python", "openai-whisper")
    .apt_install("ffmpeg")
    .run_function(download_whisper)
)


@dataclass
class PhraseBlock:
    # this is only to be more self documenting
    # in case we want to support whisper
    start: float
    end: float
    text: str = field(repr=False)
    length: int = field(init=False)

    def __post_init__(self):
        self.length = len(self.text)


def group_speech(blocks, max_chunk=30000):
    acc = blocks[0].text
    start = 0

    for a, b in zip([b for b in blocks][:-1], [b for b in blocks][1:]):
        # if there is a long pause
        # or if the speech is more than 7 second
        is_pause = (b.start - a.end) > 0.5
        is_long = b.start - start > 6
        is_too_long = len(acc) > max_chunk

        if (is_long & is_pause) | is_too_long:
            yield PhraseBlock(start=start, end=a.end, text=acc.strip())
            acc = ""
            start = b.start
        else:
            acc += " " + b.text


path = "./data/craig/mp3"
download_path = "transcripts/data/power_series/"


stub = modal.Stub(mounts=[modal.Mount(local_dir=path, remote_dir="/root/data")])


@stub.function(gpu="any", image=img, timeout=6000)
def transcribe(file):
    import logging
    import whisper

    logging.basicConfig(level=logging.INFO)

    model = whisper.load_model("large")
    audio = whisper.load_audio(file)
    result = model.transcribe(audio)
    return result["text"]


if __name__ == "__main__":
    # create the download directory if it doesn't exist
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    files = glob.glob(path + "/*.mp3")[:1]

    with stub.run():
        file_names = [f.split("/")[-1] for f in files]
        transcriptions = transcribe.map([f"/root/data/{f}" for f in file_names])
        for fn, res in zip(file_names, transcriptions):
            with open(download_path + fn + ".txt", "w") as f:
                f.write(res)
