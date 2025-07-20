from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class CASAgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    transactions: list[dict]
    curr_holdings: list[dict]
    past_holdings: list[dict]
