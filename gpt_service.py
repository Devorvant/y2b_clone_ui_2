
import os
from dotenv import load_dotenv

load_dotenv()

import openai

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

style_prompts = {
    "blog": "Напиши статью",
    "motivation": "Сделай вдохновляющий мотивационный текст",
    "story": "Сделай интересный рассказ",
    "humor": "Сделай пересказ с юмором"
}

def generate_blog(transcript: str, style: str = "blog", language: str = "русском"):
    prompt_type = style_prompts.get(style, style_prompts["blog"])
    prompt = f"{prompt_type} на {language} языке по следующему содержанию:\n\n{transcript[:3000]}"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800
    )
    return response.choices[0].message.content
