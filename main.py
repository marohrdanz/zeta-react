from typing import Annotated, TypedDict
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from os import getenv
import log_setup
from langchain_community.tools import DuckDuckGoSearchRun
from ddgs import DDGS

load_dotenv()  # Load environment variables from .env file
logger = log_setup.configure_logging()
model = getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")


# --- 1. Define Tools ---

@tool
def search(query: str) -> str:
    """Search the web for information about a topic."""
    logger.debug(f"Running search tool with query: {query}")
    try:
      with DDGS() as ddgs:
        results = ddgs.text(query, max_results=3)
        if not results:
          return "No results found."
        formatted = "\n\n".join(
            f"{r['title']}\n{r['href']}\n{r['body']}"
            for r in results
        )
        logger.debug(f"Formatted search results:\n{formatted}")
        return formatted
    except Exception as e:
      logger.error(f"Search.run failed for {query}: {e}")
      result = f"Error: {e}"
    return result

@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression. Example input: '2 + 2' or '100 * 3.14'"""
    logger.debug(f"Running calculator tool with expression: {expression}")
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {e}"

tools = [search, calculator]

# --- 2. Define Agent State ---

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# --- 3. Set Up the Model ---

model = ChatAnthropic(model=model).bind_tools(tools)

# --- 4. Define the Nodes ---

system_prompt = SystemMessage(content="""You are a helpful research assistant.
Use the search tool to look up information and the calculator tool for math.
Think step by step about what you need to do.""")

def agent_node(state: AgentState):
    """The reasoning node — calls the LLM."""
    messages = [system_prompt] + state["messages"]
    response = model.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState):
    """Decide whether to call a tool or end."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
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
logger.info("Mermaid Diagram:")
print(mermaid_code)

# --- 6. Run It ---

def run_agent(question: str):
    result = app.invoke({
        "messages": [HumanMessage(content=question)]
    })
    return result["messages"][-1].content

# Example usage
if __name__ == "__main__":
    logger.info("Starting agent...")
    response = run_agent("Who created calculus, and what is 1991 / 33?")
    print(response)

