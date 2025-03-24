from youtube_transcript_api import YouTubeTranscriptApi
import re
import requests
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем прокси из .env
PROXY = os.getenv("PROXY_URL")

# Настраиваем проксированную сессию
class ProxiedSession(requests.Session):
    def __init__(self):
        super().__init__()
        if PROXY:
            self.proxies.update({
                "http": PROXY,
                "https": PROXY
            })

# Подменяем сессию библиотеки YouTubeTranscriptApi
YouTubeTranscriptApi._session = ProxiedSession()

# Извлекаем ID видео
def extract_video_id(url: str):
    match = re.search(r"v=([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

# Получаем транскрипт
def get_transcript(url: str):
    video_id = extract_video_id(url)
    if not video_id:
        return "⚠️ Невалидная ссылка на YouTube"
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([t["text"] for t in transcript])
    except Exception as e:
        return f"❌ Ошибка при получении транскрипта: {e}"
