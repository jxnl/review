import modal 

def download_whisper():
    import whisper
    model = whisper.load_model("base")
    return 

telegram_transcribe = (
    modal.Image.debian_slim()
        .pip_install(
            "ffmpeg-python",
            "openai-whisper",
            "pyTelegramBotAPI")
        .apt_install("ffmpeg")
        .run_function(download_whisper)
)

stub = modal.Stub("modal-whisper", )


@stub.webhook(gpu="any", label="telegram-transcribe", image=telegram_transcribe, secret=modal.Secret.from_name("telegram"))
def telegram_transcribe_memo(file_id):
    import telebot
    import whisper
    import tempfile
    import os
    import logging

    logger = logging.getLogger(__name__)

    model = whisper.load_model("base")
    bot = telebot.TeleBot(os.environ["TELEGRAM_BOT_TOKEN"])

    file_info = bot.get_file(file_id)

    logger.info("Downloading file %s", file_info.file_path)
    downloaded_file = bot.download_file(file_info.file_path)

    with tempfile.TemporaryDirectory() as dirpath:
        with tempfile.NamedTemporaryFile(dir=dirpath, suffix=file_id) as temp_file:
            logger.info("Writing file to %s", temp_file.name)
            temp_file.write(downloaded_file)

            logger.info("Transcribing file %s", temp_file.name)
            audio = whisper.load_audio(temp_file.name)
            logger.info(f"Transcribing audio for %s", file_id)
            result = model.transcribe(audio)
            return result