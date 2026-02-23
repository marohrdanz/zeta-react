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
from tools import tools
from rich.console import Console
from rich.panel import Panel
from print_utils import print_agent_state

load_dotenv()  # Load environment variables from .env file
logger = log_setup.configure_logging()
model = getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
console = Console()  # For rich output

# --- Define Agent State ---

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# --- Set Up the Model ---

# .bind_tools is what connects the model to the tools, allowing
# it to decide when to call them based on the conversation.

model = ChatAnthropic(model=model).bind_tools(tools)

# --- Define the Nodes ---

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
    # if the most recent message includes a tool call, we want to go to the tool node next
    if last_message.tool_calls:
        return "tools"
    # otherwise, we assume the agent is done and we can end the execution
    return END

# --- Build the Graph ---

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

## print mermaide code for visualization in README
mermaid_code = app.get_graph().draw_mermaid()
logger.info("Mermaid Diagram (to cut-and-paste into README):")
print(mermaid_code)

# --- Run It ---

def run_agent(question: str):
    result = app.invoke({
        "messages": [HumanMessage(content=question)]
    })
    print_agent_state(result, title="Final Agent State")
    return result["messages"][-1].content

if __name__ == "__main__":
    logger.info("Starting agent...")
    question = "What the notes the C major, minor, and blues scales? What can you tell me about cool jazz?"
    response = run_agent(question)
    console.print(Panel.fit(f"Question: {question}", title="User Question", style="yellow"))
    console.print(Panel.fit(f"Response: {response}", title="Agent Response", style="cyan"))

