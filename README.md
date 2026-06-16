# MCP Chat

Lesson 3 chatbot example from the MCP course. This repo demonstrates Anthropic tool use for searching arXiv papers and extracting paper metadata — in **two ways**:

1. **Direct tool use** — the original implementation where the chatbot calls Python functions in-process.
2. **MCP client–server** — a full MCP integration where the chatbot connects to a separate MCP server over stdio.

Both chatbots expose the same capabilities (`search_papers`, `extract_info`) and use Claude (`claude-sonnet-4-6`) with the same agentic tool loop.

## Setup

1. Create and activate a virtual environment (optional if you use `uv`):

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
```

2. Install dependencies:

```bash
pip install -e .
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

3. Configure your API key:

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY
```

## Usage

### Approach 1: Direct tool use (non-MCP)

The chatbot passes tool definitions to Claude and executes tools by calling Python functions directly via `executor.py`.

```bash
mcp-chat
```

Or:

```bash
python -m mcp_chat
```

**Flow:**

```
User → Claude → execute_tool() → search_papers / extract_info (in-process)
```

### Approach 2: MCP client–server

The chatbot acts as an MCP client. It spawns an MCP server as a subprocess, discovers tools over the MCP protocol, and routes Claude's tool calls through `session.call_tool()`.

```bash
uv run mcp_chatbot.py
```

Or, with an activated venv:

```bash
python mcp_chatbot.py
```

The MCP server can also be run standalone (e.g. for MCP Inspector):

```bash
uv run research_server.py
# or
research-mcp
```

**Flow:**

```
User → Claude → MCP client → stdio → MCP server → search_papers / extract_info
```

### Example query

Works with either chatbot:

```
Search for 2 papers on "LLM interpretability"
```

Type `quit` at the prompt to exit.

## Project structure

```
mcp_chatbot.py          # MCP client chatbot (Approach 2)
research_server.py      # MCP server entry point (stdio)
src/mcp_chat/
├── tools.py            # Tool implementations + FastMCP server
├── schemas.py          # Anthropic tool definitions (Approach 1)
├── executor.py         # Direct tool dispatch (Approach 1)
├── chatbot.py          # Direct tool-use chat loop (Approach 1)
└── __main__.py         # CLI entry point for mcp-chat
```

| File | Role in Approach 1 | Role in Approach 2 |
|------|--------------------|--------------------|
| `chatbot.py` | Chat loop + Claude tool use | — |
| `schemas.py` | Tool schemas sent to Claude | — |
| `executor.py` | Runs tools in-process | — |
| `tools.py` | Tool function implementations | Same functions, exposed via FastMCP |
| `mcp_chatbot.py` | — | MCP client + Claude tool loop |
| `research_server.py` | — | Starts the MCP server |

Paper search results are saved under `papers/` at runtime (gitignored).

## When to use which

- **Direct tool use** — simpler to read and debug; good for learning Anthropic tool use without MCP.
- **MCP client–server** — matches production MCP patterns: tools run in a separate process, can be swapped or inspected independently, and work with MCP-compatible tooling (e.g. MCP Inspector).

## Resources

- [Anthropic tool use guide](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview#how-to-implement-tool-use)
- [Model Context Protocol](https://modelcontextprotocol.io/)
