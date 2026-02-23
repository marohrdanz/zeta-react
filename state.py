from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

# --- Define Agent State ---

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

