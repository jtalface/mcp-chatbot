from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from typing import List
import asyncio
import nest_asyncio

nest_asyncio.apply()

load_dotenv()

class MCP_ChatBot:

    def __init__(self):
        # Initialize session and client objects
        self.session: ClientSession = None
        self.anthropic = Anthropic()
        self.available_tools: List[dict] = []

    async def process_query(self, query):
        messages = [{"role": "user", "content": query}]
        response = self.anthropic.messages.create(
            max_tokens=2024,
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

            messages.append({"role": "assistant", "content": assistant_content})

            tool_results = []
            for tool_use in tool_uses:
                print(f"Calling tool {tool_use.name} with args {tool_use.input}")
                result = await self.session.call_tool(
                    tool_use.name, arguments=tool_use.input
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": self._format_tool_result(result),
                    }
                )

            messages.append({"role": "user", "content": tool_results})

            response = self.anthropic.messages.create(
                max_tokens=2024,
                model="claude-sonnet-4-6",
                tools=self.available_tools,
                messages=messages,
            )

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
    
    async def connect_to_server_and_run(self):
        # Create server parameters for stdio connection
        server_params = StdioServerParameters(
            command="uv",  # Executable
            args=["run", "research_server.py"],  # Optional command line arguments
            env=None,  # Optional environment variables
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                # Initialize the connection
                await session.initialize()
    
                # List available tools
                response = await session.list_tools()
                
                tools = response.tools
                print("\nConnected to server with tools:", [tool.name for tool in tools])
                
                self.available_tools = [{
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                } for tool in response.tools]
    
                await self.chat_loop()


async def main():
    chatbot = MCP_ChatBot()
    await chatbot.connect_to_server_and_run()
  

if __name__ == "__main__":
    asyncio.run(main())