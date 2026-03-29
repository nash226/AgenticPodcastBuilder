import json
from datetime import date
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from openai import OpenAI

from llm_tools import create_audio, read_webpage, search_web

load_dotenv()
llm = OpenAI()

SEARCH_WEB_TOOL = {
    "type": "function",
    "name": "search_web",
    "description": (
        "Searches the web based on a query and retrieves an array of "
        "relevant URLs."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The query of the web search",
            }
        },
        "required": ["query"],
    },
}

READ_WEBPAGE_TOOL = {
    "type": "function",
    "name": "read_webpage",
    "description": "Accesses a webpage and obtains its text.",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL of the webpage",
            }
        },
        "required": ["url"],
    },
}

CREATE_AUDIO_TOOL = {
    "type": "function",
    "name": "create_audio",
    "description": (
        "Uses text-to-speech to convert a podcast script into an MP3 "
        "podcast named podcast.mp3."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "script": {
                "type": "string",
                "description": "A podcast script read by a single host",
            }
        },
        "required": ["script"],
    },
}

TOOLS = [
    SEARCH_WEB_TOOL,
    READ_WEBPAGE_TOOL,
    CREATE_AUDIO_TOOL,
]

PODCAST_RESEARCH_TOOLS = [
    SEARCH_WEB_TOOL,
    READ_WEBPAGE_TOOL,
]

TOOL_FUNCTIONS = {
    "search_web": search_web,
    "read_webpage": read_webpage,
    "create_audio": create_audio,
}


SYSTEM_PROMPT = f"""You are an AI assistant.
You have access to several specialized tools. Today's date is {date.today().strftime("%B %d, %Y")}.
Here are your tools:
<tools>
* With the search_web tool, you have the ability to search the web based on a
query and retrieve URLs of web pages relevant to that query. This is
especially useful for current information and information you do not possess
in your internal knowledge.
* With the read_webpage tool, you have the ability to read the text from a
web page of any given URL. This is useful in conjunction with the search_web
tool. That is, the search_web tool retrieves URLs, and the read_webpage tool
can read the text contained at those web pages.
* With the create_audio tool, you can convert a podcast script into an audio
MP3 podcast.
</tools>
When a user asks you to do something, think through whether tools are
necessary before using them. If they are, make a brief plan and then execute
it.
"""

def llm_response(prompt, tools):
    return llm.responses.create(
        model="gpt-5-mini",
        tools=tools,
        input=prompt,
    )


def run_tool_call(tool_call):
    function_name = tool_call.name
    function = TOOL_FUNCTIONS.get(function_name)
    if function is None:
        raise ValueError(f"Unsupported tool requested: {function_name}")

    args = json.loads(tool_call.arguments)
    try:
        result = {function_name: function(**args)}
    except Exception as exc:
        result = {
            "error": f"Tool '{function_name}' failed: {exc}",
            "tool_name": function_name,
        }
    return {
        "type": "function_call_output",
        "call_id": tool_call.call_id,
        "output": json.dumps(result),
    }


def build_history():
    return [
        {"role": "developer", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": "How can I help you today?"},
    ]


def get_assistant_response(history, tools=TOOLS):
    while True:
        response = llm_response(history, tools)
        history.extend(response.output)
        tool_calls = [
            obj
            for obj in response.output
            if getattr(obj, "type", None) == "function_call"
        ]

        if not tool_calls:
            history.append({"role": "assistant", "content": response.output_text})
            return response.output_text, history

        for tool_call in tool_calls:
            history.append(run_tool_call(tool_call))


def build_podcast_script(topic, duration_minutes):
    history = [
        {
            "role": "developer",
            "content": (
                f"You are a podcast writer. Today's date is "
                f"{date.today().strftime('%B %d, %Y')}. "
                "Use web research tools when necessary. First think through a "
                "brief plan. Then produce a single polished podcast script for "
                "one host. Do not call create_audio. Do not include stage "
                "directions, markdown formatting, or meta commentary."
            ),
        }
    ]
    history.append(
        {
            "role": "user",
            "content": (
                f"Create a podcast script about {topic}. The target runtime is "
                f"about {duration_minutes} minutes. Research current details if "
                "needed and return only the final script."
            ),
        }
    )
    script, _ = get_assistant_response(history, tools=PODCAST_RESEARCH_TOOLS)
    return script


def generate_podcast(topic, duration_minutes):
    script = build_podcast_script(topic, duration_minutes)
    output_dir = Path("generated_podcasts")
    filename = output_dir / f"podcast_{uuid4().hex}.mp3"
    audio_path = create_audio(script, audio_filename=filename)
    return script, audio_path


def main():
    print("Assistant: How can I help you today?\n")
    history = build_history()

    while True:
        try:
            user_input = input("User: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if user_input.lower() == "exit":
            break
        if not user_input:
            continue

        history.append({"role": "user", "content": user_input})

        try:
            assistant_text, history = get_assistant_response(history)
            print(f"\nAssistant: {assistant_text}\n")
        except Exception as exc:
            message = f"Sorry, something went wrong: {exc}"
            print(f"\nAssistant: {message}\n")
            history.append({"role": "assistant", "content": message})
 
 
if __name__ == "__main__":
    main()
