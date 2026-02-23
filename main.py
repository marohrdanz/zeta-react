from typing import Annotated, TypedDict
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from os import getenv
import log_setup
from langchain_community.tools import DuckDuckGoSearchRun
from ddgs import DDGS
import json
import re
from colorama import Fore, Back, Style, init
from rich.console import Console
from rich.panel import Panel

load_dotenv()  # Load environment variables from .env file
logger = log_setup.configure_logging()
model = getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
console = Console()  # For rich output


# --- 1. Define Tools ---

# The docstrings are important for the model to understand how to use the tools,
# so be sure to include clear instructions and examples.
# The @tool decorator is what makes these functions available as tools that
# the model can call during the conversation.

@tool
def get_major_scale(key: str) -> list[str]:
    """Given a musical key, return the major scale for that key.

    Example input: 'C'

    Example output for 'C': ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    """
    # All notes in chromatic scale (using sharps)
    chromatic = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    # Enharmonic equivalents (flat -> sharp)
    enharmonic = {
        "Db": "C#", "Eb": "D#", "Fb": "E", "Gb": "F#",
        "Ab": "G#", "Bb": "A#", "Cb": "B"
    }

    # Major scale interval pattern: W W H W W W H
    # (in semitones: 2 2 1 2 2 2 1)
    intervals = [2, 2, 1, 2, 2, 2, 1]

    # Normalize the key
    key = key.strip().capitalize()
    if len(key) > 1:
        key = key[0].upper() + key[1:].lower()
    key = enharmonic.get(key, key)

    if key not in chromatic:
        raise ValueError(f"Invalid key: '{key}'. Use note names like C, D#, Bb, etc.")

    # Build the scale
    start = chromatic.index(key)
    scale = []
    pos = start
    for interval in intervals:
        scale.append(chromatic[pos % 12])
        pos += interval

    return scale

@tool
def get_blues_scale(key: str) -> list[str]:
    """Given a musical key, return the blues scale for that key.

    Example input: 'C'

    Example output for 'C': ['C', 'Eb', 'F', 'Gb', 'G', 'Bb']
    """
    # All notes in chromatic scale
    chromatic = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    # Enharmonic equivalents (flat -> sharp)
    enharmonic = {
        "Db": "C#", "Eb": "D#", "Fb": "E", "Gb": "F#",
        "Ab": "G#", "Bb": "A#", "Cb": "B"
    }

    # Blues scale intervals (semitones): 3 2 1 1 3 2
    # Formula: Root, b3, 4, b5, 5, b7, Root
    intervals = [3, 2, 1, 1, 3, 2]

    # Normalize the key
    key = key.strip()
    if len(key) > 1:
        key = key[0].upper() + key[1:].lower()
    else:
        key = key.upper()
    key = enharmonic.get(key, key)

    if key not in chromatic:
        raise ValueError(f"Invalid key: '{key}'. Use note names like C, D#, Bb, etc.")

    # Build the scale
    start = chromatic.index(key)
    scale = []
    pos = start
    for interval in intervals:
        scale.append(chromatic[pos % 12])
        pos += interval

    return scale


@tool
def search(query: str) -> str:
    """Search the web for information about a topic."""
    try:
      with DDGS() as ddgs:
        results = ddgs.text(query, max_results=3)
        if not results:
          return "No results found."
        formatted = "\n\n".join(
            f"{r['title']}\n{r['href']}\n{r['body']}"
            for r in results
        )
        return formatted
    except Exception as e:
      logger.error(f"Search.run failed for {query}: {e}")
      result = f"Error: {e}"
    return result


tools = [search, get_major_scale, get_blues_scale]

# --- 2. Define Agent State ---

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# --- 3. Set Up the Model ---

# .bind_tools is what connects the model to the tools, allowing
# it to decide when to call them based on the conversation.

model = ChatAnthropic(model=model).bind_tools(tools)

# --- 4. Define the Nodes ---

system_prompt = SystemMessage(content="""You are a Miles Davis.
Use the search tool to look up information, the get_major_scale tool to get notes
in a major scale, and get_blues_scale to get notes in the blues scale.
Think step by step about what you need to do.""")

def agent_node(state: AgentState):
    """The reasoning node — calls the LLM."""
    print_agent_state(state, title="Agent State Before LLM Call")
    messages = [system_prompt] + state["messages"]
    response = model.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState):
    """Decide whether to call a tool or end."""
    print_agent_state(state, title="Agent State Before Decision")
    last_message = state["messages"][-1]
    logger.debug(f"last_message: {last_message}")
    # if the most recent message includes a tool call, we want to go to the tool node next
    if last_message.tool_calls:
        return "tools"
    # otherwise, we assume the agent is done and we can end the execution
    return END

# --- 5. Build the Graph ---

tool_node = ToolNode(tools)

graph = StateGraph(AgentState)

graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)

graph.set_entry_point("agent")

graph.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", END: END}
)

graph.add_edge("tools", "agent")  # After tool call, go back to agent

app = graph.compile()
mermaid_code = app.get_graph().draw_mermaid()
logger.info("Mermaid Diagram (to cut-and-paste into README):")
print(mermaid_code)

# --- 6. Run It ---

def run_agent(question: str):
    result = app.invoke({
        "messages": [HumanMessage(content=question)]
    })
    print_agent_state(result, title="Final Agent State")
    return result["messages"][-1].content

# -- debugging help --

init(autoreset=True)  # Initialize colorama for colored output
COLORS = {
    "HUMAN": Fore.GREEN,
    "AI": Fore.CYAN,
    "TOOL": Fore.YELLOW,
    "CONTENT": Fore.WHITE
}

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

def print_agent_state(state: AgentState, title: str = "Agent State"):
    """Pretty print the AgentState for debugging."""
    
    messages = state.get("messages", [])
    console.print(Panel.fit(f"Total messages: {len(messages)}", title=f"{title}", style="magenta"))
    
    for i, msg in enumerate(messages):
        # Determine message type and label
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
        
    
    print()

# Example usage
if __name__ == "__main__":
    logger.info("Starting agent...")
    question = "What the notes the C major, minor, and blues scales? What can you tell me about cool jazz?"
    response = run_agent(question)
    console.print(Panel.fit(f"Question: {question}", title="User Question", style="yellow"))
    console.print(Panel.fit(f"Response: {response}", title="Agent Response", style="cyan"))

