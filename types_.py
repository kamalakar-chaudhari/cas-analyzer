from typing import TypedDict

from langchain_core.messages import AnyMessage


class CASAgentState(TypedDict):
    messages: list[AnyMessage]
    transactions: list[dict]
    curr_holdings: list[dict]
    past_holdings: list[dict]
