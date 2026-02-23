from rich.console import Console
from rich.panel import Panel
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage, SystemMessage, ToolMessage
from colorama import Fore, Back, Style, init
import json
import re

#
# Some debugging utilities to print out the AgentState in a more readable format, with colors and formatting.
#
# These are pretty sloppy...but I'm not going to take the time to clean them now.
#

init(autoreset=True)  # Initialize colorama for colored output
COLORS = {
    "HUMAN": Fore.GREEN,
    "AI": Fore.CYAN,
    "TOOL": Fore.YELLOW,
    "CONTENT": Fore.WHITE
}

def print_agent_state(state: AgentState, title: str = "Agent State"):
    """Pretty print the AgentState for debugging."""
    console = Console()   
    messages = state.get("messages", [])
    console.print(Panel.fit(f"Total messages: {len(messages)}", title=f"{title}", style="magenta"))

    for i, msg in enumerate(messages):
        # Determine message type and label (for once those AI-emoji are useful, lolz)
        if isinstance(msg, HumanMessage):
            role = "🧑 HUMAN"
        elif isinstance(msg, AIMessage):
            role = "🤖 AI"
        elif isinstance(msg, ToolMessage):
            role = "🔧 TOOL"
        elif isinstance(msg, SystemMessage):
            role = "⚙️  SYSTEM"
        else:
            role = f"❓ {type(msg).__name__.upper()}"

    console.print(f"\n  [{i}] {role}", style="magenta")

    # Print content
    if msg.content:
        formatted_content = format_content(msg.content)
    indented_content = "\n".join("    " + line for line in formatted_content.splitlines())
    print(f"  Content:\n {COLORS['CONTENT']}{indented_content}")

    # Print tool calls (on AI messages)
    if isinstance(msg, AIMessage) and msg.tool_calls:
        print(f"  Tool Calls:")
        for tc in msg.tool_calls:
            args_str = json.dumps(tc.get("args", {}), indent=10)
            print(f" {COLORS['TOOL']} {tc['name']}()")
            print(f" {COLORS['TOOL']}     Args: {args_str}")
            print(f" {COLORS['TOOL']}     ID:   {tc['id']}")

    # Print tool result metadata
    if isinstance(msg, ToolMessage):
        print(f"  Tool Name: {COLORS['TOOL']}{msg.name}")
        print(f"  Tool ID:   {COLORS['TOOL']}{msg.tool_call_id}")

def format_content(content) -> str:
    """Attempt to pretty-print content, handling text, JSON, and mixed strings."""

    # Handle list content (some LangChain messages use a list of blocks)
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(json.dumps(block, indent=4))
            else:
                parts.append(str(block))
        return "\n".join(parts)

    if not isinstance(content, str):
        return str(content)

    # Try parsing the whole thing as JSON first
    try:
        parsed = json.loads(content)
        return json.dumps(parsed, indent=4)
    except json.JSONDecodeError:
        pass

    # Look for embedded JSON blobs inside a string and pretty-print them
    def pretty_json_match(match):
        try:
            parsed = json.loads(match.group(0))
            return json.dumps(parsed, indent=4)
        except json.JSONDecodeError:
            return match.group(0)
    
    content = re.sub(r'\{.*?\}|\[.*?\]', pretty_json_match, content, flags=re.DOTALL)
    
    return content

