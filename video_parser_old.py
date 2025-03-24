
from youtube_transcript_api import YouTubeTranscriptApi
import re

def extract_video_id(url: str):
    match = re.search(r"v=([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

def get_transcript(url: str):
    video_id = extract_video_id(url)
    if not video_id:
        return "⚠️ Невалидная ссылка на YouTube"
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    return " ".join([t["text"] for t in transcript])
