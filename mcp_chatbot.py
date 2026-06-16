from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from typing import List, Dict, TypedDict
from contextlib import AsyncExitStack
import json
import asyncio

load_dotenv()

MAX_TOKENS = 8192

class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict

class MCP_ChatBot:

    def __init__(self):
        # Initialize session and client objects
        self.sessions: List[ClientSession] = [] # new
        self.exit_stack = AsyncExitStack() # new
        self.anthropic = Anthropic()
        self.available_tools: List[ToolDefinition] = [] # new
        self.tool_to_session: Dict[str, ClientSession] = {} # new


    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a single MCP server."""
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            ) # new
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            ) # new
            await session.initialize()
            self.sessions.append(session)
            
            # List available tools for this session
            response = await session.list_tools()
            tools = response.tools
            print(f"\nConnected to {server_name} with tools:", [t.name for t in tools])
            
            for tool in tools: # new
                self.tool_to_session[tool.name] = session
                self.available_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")

    async def connect_to_servers(self): # new
        """Connect to all configured MCP servers."""
        try:
            with open("server_config.json", "r") as file:
                data = json.load(file)
            
            servers = data.get("mcpServers", {})
            
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
        except Exception as e:
            print(f"Error loading server configuration: {e}")
            raise
    
    async def process_query(self, query):
        messages = [{"role": "user", "content": query}]
        response = self.anthropic.messages.create(
            max_tokens=MAX_TOKENS,
            model="claude-sonnet-4-6",
            tools=self.available_tools,
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

            if response.stop_reason == "max_tokens":
                print(
                    "Warning: response hit max_tokens and may include incomplete tool calls. "
                    "Retry the query or increase MAX_TOKENS."
                )

            messages.append({"role": "assistant", "content": assistant_content})

            tool_results = []
            for tool_use in tool_uses:
                print(f"Calling tool {tool_use.name} with args {self._summarize_tool_args(tool_use.input)}")
                try:
                    session = self.tool_to_session[tool_use.name]
                    result = await session.call_tool(
                        tool_use.name, arguments=tool_use.input
                    )
                    formatted = self._format_tool_result(result)
                    if result.isError:
                        print(f"Tool error ({tool_use.name}): {formatted}")
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": formatted,
                            "is_error": result.isError,
                        }
                    )
                except Exception as e:
                    error_message = f"Tool execution failed: {e}"
                    print(f"Tool error ({tool_use.name}): {error_message}")
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": error_message,
                            "is_error": True,
                        }
                    )

            messages.append({"role": "user", "content": tool_results})

            response = self.anthropic.messages.create(
                max_tokens=MAX_TOKENS,
                model="claude-sonnet-4-6",
                tools=self.available_tools,
                messages=messages,
            )

    def _summarize_tool_args(self, args: dict) -> dict:
        """Summarize tool args for logging without dumping huge content payloads."""
        summary = {}
        for key, value in args.items():
            if isinstance(value, str) and len(value) > 120:
                summary[key] = f"<string, {len(value)} chars>"
            else:
                summary[key] = value
        return summary

    def _format_tool_result(self, result: types.CallToolResult) -> str:
        if not result.content:
            return "The operation completed but didn't return any results."

        parts = []
        for block in result.content:
            if hasattr(block, "text"):
                parts.append(block.text)
            else:
                parts.append(str(block))

        return "\n".join(parts)

    
    
    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
        
                if query.lower() == 'quit':
                    break
                    
                await self.process_query(query)
                print("\n")
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self): # new
        """Cleanly close all resources using AsyncExitStack."""
        await self.exit_stack.aclose()


async def main():
    chatbot = MCP_ChatBot()
    try:
        # the mcp clients and sessions are not initialized using "with"
        # like in the previous lesson
        # so the cleanup should be manually handled
        await chatbot.connect_to_servers() # new! 
        await chatbot.chat_loop()
    finally:
        await chatbot.cleanup() #new! 


if __name__ == "__main__":
    asyncio.run(main())