import json
from datetime import date

from dotenv import load_dotenv
from openai import OpenAI

from llm_tools import create_audio, read_webpage, search_web

load_dotenv()
llm = OpenAI()

TOOLS = [
    {
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
    },
    {
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
    },
    {
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
    },
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
query and retrieve urls of web pages relevant to that query. This is
especially useful for searching for current information and information you
don't possess in your internal knowledge.
* With the read_webpage tool, you have the ability to read the text from a
web page of any given url. This is a useful tool to use in conjunction with
the search_web tool. That is, the search_web tool retrieves urls, and the
read_webpage tool can read the text contained at those web pages.
* With the create_audio tool, you can convert a podcast script text into an
audio mp3 podcast.
</tools>
When a user asks you to do something, don't use tools without first thinking.
Rather, first generate a comprehensive plan as to how you'll use the tools (if
at all) to accomplish the user's goal. Then, follow your plan using the tools.
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
    result = {function_name: function(**args)}
    return {
        "type": "function_call_output",
        "call_id": tool_call.call_id,
        "output": json.dumps(result),
    }


def main():
    print("Assistant: How can I help you today?\n")
    history = [
        {"role": "developer", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": "How can I help you today?"},
    ]

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
            while True:
                response = llm_response(history, TOOLS)
                history.extend(response.output)
                tool_calls = [
                    obj
                    for obj in response.output
                    if getattr(obj, "type", None) == "function_call"
                ]

                if not tool_calls:
                    print(f"\nAssistant: {response.output_text}\n")
                    history.append(
                        {"role": "assistant", "content": response.output_text}
                    )
                    break

                for tool_call in tool_calls:
                    history.append(run_tool_call(tool_call))
        except Exception as exc:
            message = f"Sorry, something went wrong: {exc}"
            print(f"\nAssistant: {message}\n")
            history.append({"role": "assistant", "content": message})


if __name__ == "__main__":
    main()
