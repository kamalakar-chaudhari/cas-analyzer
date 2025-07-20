import sqlite3
from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

# from langgraph.graph import MessagesState
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt.tool_node import ToolNode

from services.openai_service import OpenAIService


class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    transactions: list[dict]
    curr_holdings: list[dict]
    past_holdings: list[dict]


@tool
def multiply(x: int, y: int) -> int:
    """multiply two integers and return result"""
    print("multiply called")
    return x * y


@tool
def add(x: int, y: int) -> int:
    """Add two integers and return result"""
    print("add called")
    return x + y


llm_with_tools = ChatOpenAI(temperature=0, model="gpt-4").bind_tools([multiply, add])


def llm_node(state: MessagesState):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


tool_node = ToolNode([multiply, add])


graph_builder = StateGraph(MessagesState)
graph_builder.add_node("llm_node", llm_node)
graph_builder.add_node("tools", tool_node)

graph_builder.set_entry_point("llm_node")
graph_builder.add_conditional_edges("llm_node", tools_condition)
graph_builder.add_edge("tools", "llm_node")
graph_builder.set_finish_point("llm_node")

conn = sqlite3.connect("./data/checkpoints.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)
agent = graph_builder.compile(checkpointer=memory)


class PFAnalyzerGraphAgent:
    def __init__(self, session_id: str, llm: OpenAIService, tools: list | None = None):
        self.llm = llm
        self.tools = tools
        self.session_id = session_id

    async def ask(self, query):
        result = agent.invoke(
            {"messages": [HumanMessage(query)]},
            {"configurable": {"thread_id": self.session_id}},
        )
        return result["messages"][-1].content
