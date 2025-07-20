import json
import sqlite3

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage, SystemMessage

from types_ import CASAgentState
from domain.cas_parser import CasParser
from utils.db_utils import get_sqlite_connection

PORTFOLIO_SUMMARY_PROMPT = """
    You are a portfolio summarizer.

    ## Inputs

    You will be given two tables:

    ### 1. Current Holdings
    - Each row contains: scheme name, ISIN, units held, invested amount, and current market value.
    - Your task: For each scheme, calculate:
    - Absolute gain = market value − amount
    - Percentage gain = (gain / amount) × 100
    - Output: A markdown table with scheme name, amount, market value, absolute gain, and percentage gain.

    ### 2. Past Holdings
    - This table contains schemes the user had invested in previously but currently holds zero units.
    - Your task: List only the scheme names in a simple markdown table.

    ## Guidelines

    - Return both tables in markdown format.
    - At the top, include a brief description of what "current holdings" and "past holdings" represent.
"""


llm_with_tools = ChatOpenAI(temperature=0, model="gpt-4")


def portfolio_summary_node(state: CASAgentState):
    from config.app_context import llm

    holdings = {
        "curr_holdings": state["curr_holdings"],
        "past_holdings": state["past_holdings"],
    }

    holdings_as_json_str = f"```json\n{json.dumps(holdings, indent=2)}\n```"

    messages = [
        SystemMessage(PORTFOLIO_SUMMARY_PROMPT),
        HumanMessage(f"Here are my holdings:\n{holdings_as_json_str}"),
    ]
    return {"messages": [llm_with_tools.invoke(messages)]}


class CasETLWorkflow:
    def __init__(self):
        graph_builder = StateGraph(CASAgentState)
        # graph_builder.add_node("cas_parser_node", cas_parser_node)
        graph_builder.add_node("portfolio_summary_node", portfolio_summary_node)

        graph_builder.set_entry_point("portfolio_summary_node")
        # graph_builder.add_edge("cas_parser_node", "portfolio_summary_node")
        graph_builder.set_finish_point("portfolio_summary_node")

        with get_sqlite_connection() as conn:
            memory = SqliteSaver(conn)
            self.agent = graph_builder.compile(checkpointer=memory)

    def _parse_cas(self, cas_file_stream, password):
        cas_parser = CasParser(cas_file_stream, password)
        transactions, curr_holdings, past_holdings = cas_parser.parse()
        return {
            "transactions": transactions,
            "curr_holdings": curr_holdings,
            "past_holdings": past_holdings,
        }

    def invoke(self, session_id, cas_file_stream, password):
        pf_details = self._parse_cas(cas_file_stream, password)
        config = {"configurable": {"thread_id": session_id}}
        self.agent.update_state(config, pf_details)
        result = self.agent.invoke({}, config=config)
        return result["messages"][-1].content
