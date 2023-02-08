import glob
import modal 

def download_whisper():
    import whisper
    whisper.load_model("large")
    return 

transcribe = (
    modal.Image.debian_slim()
        .pip_install(
            "ffmpeg-python",
            "openai-whisper")
        .apt_install("ffmpeg")
        .run_function(download_whisper)
)

stub = modal.Stub(mounts=[modal.Mount(local_dir="./data", remote_dir="/root/data")])


@stub.function(gpu="any", image=transcribe, timeout=36000)
def transcribe(file):
    import logging 
    logging.basicConfig(level=logging.INFO)
    import whisper
    logging.info(f"Transcribing {file}")
    model = whisper.load_model("large")
    audio = whisper.load_audio(file)
    result = model.transcribe(audio)
    return result["text"]


if __name__ == "__main__":
    files = glob.glob("data/*.mp3")
    print(files)

    transcriped_files = glob.glob("transcripts/data/**/*.txt")
    print(transcriped_files)

    # Remove files that have already been transcribed
    files = [f for f in files if f"{f.split('/')[-1]}.txt" not in transcriped_files]

    print(f"Transcribing {len(files)} files")

    """
    with stub.run():
        transcriptions = transcribe.map([f"/root/{f}" for f in files])
        for fn, result in zip(files, transcriptions):
            with open("transcripts/" + fn + ".txt", "w") as f:
                f.write(result)
    """