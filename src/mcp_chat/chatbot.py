from typing import Optional

import anthropic
from dotenv import load_dotenv

from mcp_chat.executor import execute_tool
from mcp_chat.schemas import tools

MODEL = "claude-sonnet-4-6"


def create_client() -> anthropic.Anthropic:
    load_dotenv()
    return anthropic.Anthropic()


def process_query(client: anthropic.Anthropic, query: str) -> None:
    messages = [{"role": "user", "content": query}]

    response = client.messages.create(
        max_tokens=2024,
        model=MODEL,
        tools=tools,
        messages=messages,
    )

    while True:
        assistant_content = []
        tool_uses = []

        for content in response.content:
            if content.type == "text":
                print(content.text)
                assistant_content.append(content)
            elif content.type == "tool_use":
                assistant_content.append(content)
                tool_uses.append(content)

        if not tool_uses:
            break

        messages.append({"role": "assistant", "content": assistant_content})

        tool_results = []
        for tool_use in tool_uses:
            print(f"Calling tool {tool_use.name} with args {tool_use.input}")
            result = execute_tool(tool_use.name, tool_use.input)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result,
                }
            )

        messages.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            max_tokens=2024,
            model=MODEL,
            tools=tools,
            messages=messages,
        )


def chat_loop(client: Optional[anthropic.Anthropic] = None) -> None:
    if client is None:
        client = create_client()

    print("Type your queries or 'quit' to exit.")
    while True:
        try:
            query = input("\nQuery: ").strip()
            if query.lower() == "quit":
                break

            process_query(client, query)
            print("\n")
        except Exception as e:
            print(f"\nError: {str(e)}")
