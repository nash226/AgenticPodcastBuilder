# Agentic Podcast Builder

## About

Agentic Podcast Builder is a Python chatbot that researches a topic on the web, reads relevant pages, and generates a podcast-style MP3 from the final script. It uses the OpenAI Responses API for tool-calling, Google Custom Search for live web results, and OpenAI text-to-speech to produce the finished audio file.

## Features

- Chat-based interface in the terminal
- Web interface built with Gradio
- Web search through Google Custom Search
- Webpage text extraction for live research
- Podcast audio generation saved as downloadable MP3 files
- Environment-based configuration with `.env`

## Requirements

- Python 3
- An OpenAI API key
- A Google Custom Search API key
- A Google Custom Search Engine ID

## Installation

Create and activate the virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python3 -m pip install openai python-dotenv requests beautifulsoup4
```

Or install from the project file:

```bash
python3 -m pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root with:

```env
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
SEARCH_ENGINE_ID=your_search_engine_id
```

You can start from the included template:

```bash
cp .env.example .env
```

## Run

From the project root, run:

```bash
python3 chatbot.py
```

Type `exit` to end the chat.

To launch the web interface:

```bash
python3 gradio_app.py
```

Gradio will print a local URL in the terminal. Open that URL in your browser to
generate and download MP3 files.

## Testing

Run the unit tests with:

```bash
python3 -m unittest
```

## Project Files

- `chatbot.py`: main terminal chatbot loop
- `gradio_app.py`: Gradio web interface for generating downloadable MP3s
- `llm_tools.py`: tool implementations for search, webpage reading, and audio generation

## Output

When audio generation is triggered, the app writes the result to:

```text
generated_podcasts/
```
