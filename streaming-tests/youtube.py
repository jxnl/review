from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url):
    import re

    match = re.search(
        r"^(?:https?:\/\/)?(?:www\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))((\w|-){11})(?:\S+)?$",
        url,
    )
    if match:
        return match.group(1)
    return None


def transcribe_youtube(video_id):
    # assigning srt variable with the list
    # of dictionaries obtained by the get_transcript() function
    srt = YouTubeTranscriptApi.get_transcript(video_id)
    # prints the result
    return " ".join([s["text"] for s in srt])
