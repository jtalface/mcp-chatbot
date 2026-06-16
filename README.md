# MCP Chatbot

This repo demonstrates Anthropic tool use for searching arXiv papers and extracting paper metadata — in **two ways**:

1. **Direct tool use** — the original implementation where the chatbot calls Python functions in-process.
2. **MCP client–server** — a progressive set of MCP clients that connect to one or more MCP servers over stdio.

Both approaches use Claude with an agentic tool loop. The MCP path builds in three stages (`mcp_chatbot-00.py` → `01` → `02`), each adding more MCP capabilities.

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

Three client versions are provided, each building on the previous lesson:

| File | What it adds |
|------|--------------|
| `mcp_chatbot-00.py` | Single MCP server (research tools only) |
| `mcp_chatbot-01.py` | Multiple MCP servers via `server_config.json` (filesystem, research, fetch) |
| `mcp_chatbot-02.py` | Resources and prompts — browse saved papers with `@` syntax and run server prompts with `/prompt` |

Run any version with:

```bash
uv run mcp_chatbot-00.py
uv run mcp_chatbot-01.py
uv run mcp_chatbot-02.py
```

Or, with an activated venv:

```bash
python mcp_chatbot-01.py
```

#### `mcp_chatbot-00.py` — single server

Connects to the research MCP server only (`search_papers`, `extract_info`).

**Flow:**

```
User → Claude → MCP client → stdio → research server → search_papers / extract_info
```

#### `mcp_chatbot-01.py` — multi-server tools

Loads all servers from `server_config.json` and routes tool calls to the correct session. Includes parallel tool-call handling, MCP error surfacing, and a higher token limit for large file writes.

Configured servers:

| Server | Tools |
|--------|-------|
| `filesystem` | read/write files, list directories |
| `research` | `search_papers`, `extract_info` |
| `fetch` | fetch web page content |

**Flow:**

```
User → Claude → MCP client → stdio → [filesystem | research | fetch] servers
```

#### `mcp_chatbot-02.py` — resources and prompts

Extends the multi-server client with MCP **resources** and **prompts** from the research server.

Interactive commands in the chat loop:

| Command | Description |
|---------|-------------|
| `@folders` | List saved paper topic folders |
| `@<topic>` | Show papers saved for a topic (e.g. `@llm_interpretability`) |
| `/prompts` | List available MCP prompts |
| `/prompt <name> <arg=value>` | Execute a prompt (e.g. `/prompt generate_search_prompt topic=transformers num_papers=3`) |

**Flow:**

```
User → @resource or /prompt → MCP client → read_resource / get_prompt
User → query       → Claude → MCP client → call_tool → server
```

### MCP server (standalone)

The research server can be run on its own (e.g. for MCP Inspector):

```bash
uv run research_server.py
# or
research-mcp
```

It exposes:

- **Tools:** `search_papers`, `extract_info`
- **Resources:** `papers://folders`, `papers://{topic}`
- **Prompts:** `generate_search_prompt`

### Example queries

Direct or MCP tool use:

```
Search for 2 papers on "LLM interpretability"
```

Multi-server (`mcp_chatbot-01.py` or `02`):

```
Fetch the content of https://modelcontextprotocol.io/docs/concepts/architecture and save it to mcp_summary.md
```

Resources and prompts (`mcp_chatbot-02.py`):

```
@folders
@llm_interpretability
/prompt generate_search_prompt topic=agentic workflows num_papers=3
```

Type `quit` at the prompt to exit.

## Project structure

```
mcp_chatbot-00.py     # MCP client — single server
mcp_chatbot-01.py     # MCP client — multi-server tools
mcp_chatbot-02.py     # MCP client — multi-server tools + resources + prompts
server_config.json    # MCP server definitions for 01 and 02
research_server.py    # MCP server entry point (stdio)
src/mcp_chat/
├── tools.py            # Tool implementations + FastMCP server (tools, resources, prompts)
├── schemas.py          # Anthropic tool definitions (Approach 1)
├── executor.py         # Direct tool dispatch (Approach 1)
├── chatbot.py          # Direct tool-use chat loop (Approach 1)
└── __main__.py         # CLI entry point for mcp-chat
```

| File | Approach 1 | MCP 00 | MCP 01 | MCP 02 |
|------|-----------|--------|--------|--------|
| `chatbot.py` | Chat loop + Claude tool use | — | — | — |
| `schemas.py` | Tool schemas sent to Claude | — | — | — |
| `executor.py` | Runs tools in-process | — | — | — |
| `tools.py` | Tool implementations | FastMCP server | FastMCP server | + resources & prompts |
| `mcp_chatbot-00.py` | — | Single-server client | — | — |
| `mcp_chatbot-01.py` | — | — | Multi-server client | — |
| `mcp_chatbot-02.py` | — | — | — | + resources & prompts |
| `server_config.json` | — | — | Server config | Server config |
| `research_server.py` | — | Server entry | Server entry | Server entry |

Paper search results are saved under `papers/` at runtime (gitignored).

## When to use which

- **Direct tool use (`mcp-chat`)** — simplest to read and debug; good for learning Anthropic tool use without MCP.
- **`mcp_chatbot-00.py`** — learn the basic MCP client–server handshake with one server.
- **`mcp_chatbot-01.py`** — production-style multi-server setup with filesystem, fetch, and research tools.
- **`mcp_chatbot-02.py`** — full MCP primitives: tools, resources, and prompts in one interactive client.

## Resources

- [Anthropic tool use guide](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview#how-to-implement-tool-use)
- [Model Context Protocol](https://modelcontextprotocol.io/)
