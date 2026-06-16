# MCP Chat

Lesson 3 chatbot example from the MCP course. This project demonstrates tool use with the Anthropic API: searching arXiv papers and extracting paper metadata via a conversational chatbot.

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
```

2. Install dependencies:

```bash
pip install -e .
```

3. Configure your API key:

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY
```

## Usage

Run the interactive chatbot:

```bash
mcp-chat
```

Or:

```bash
python -m mcp_chat
```

Type your queries at the prompt. Type `quit` to exit.

### Example query

```
Search for 2 papers on "LLM interpretability"
```

## Project structure

```
src/mcp_chat/
├── tools.py      # search_papers and extract_info tool functions
├── schemas.py    # Anthropic tool definitions
├── executor.py   # Tool mapping and execution
├── chatbot.py    # Query processing and chat loop
└── __main__.py   # CLI entry point
```

Paper search results are saved under `papers/` at runtime (gitignored).

## Resources

- [Anthropic tool use guide](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview#how-to-implement-tool-use)
