import os
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()
REQUEST_TIMEOUT_SECONDS = 20


def _require_env_vars(*names):
    missing = [name for name in names if not os.getenv(name)]
    if missing:
        missing_vars = ", ".join(missing)
        raise ValueError(f"Missing required environment variable(s): {missing_vars}")


def read_webpage(url):
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def search_web(query):
    _require_env_vars("GOOGLE_API_KEY", "SEARCH_ENGINE_ID")

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": os.getenv("GOOGLE_API_KEY"),
        "cx": os.getenv("SEARCH_ENGINE_ID"),
        "q": query,
        "num": 5,
    }

    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    items = response.json().get("items") or []
    return [item["link"] for item in items if item.get("link")]


def create_audio(script, audio_filename="podcast.mp3"):
    _require_env_vars("OPENAI_API_KEY")

    output_path = Path(audio_filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="ballad",
        instructions="""Persona: You are a newscaster.
                        Delivery: Crisp and articulate, with measured pacing.
                        Tone: Objective and neutral, confident and
                        authoritative, conversational yet formal.""",
        input=script,
    ) as response:
        response.stream_to_file(str(output_path))

    return str(output_path)
