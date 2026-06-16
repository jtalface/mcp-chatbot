import json

from mcp_chat.tools import extract_info, search_papers

mapping_tool_function = {
    "search_papers": search_papers,
    "extract_info": extract_info,
}


def execute_tool(tool_name: str, tool_args: dict) -> str:
    result = mapping_tool_function[tool_name](**tool_args)

    if result is None:
        result = "The operation completed but didn't return any results."
    elif isinstance(result, list):
        result = ", ".join(result)
    elif isinstance(result, dict):
        result = json.dumps(result, indent=2)
    else:
        result = str(result)

    return result
