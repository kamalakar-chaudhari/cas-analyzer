import json

from tools import xirr_tool
from app_context import session_service

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

PORTFOLIO_QUERY_PROMPT = """
    You are a router that decides which tool to use to answer the user's question.

    Available tools:
    - get_xirr()
    - get_total_return()
    - get_cap_composition()

    Instructions:
    - Identify the best tool
    - Return only this JSON:
    {
        "tool_name": "...",
        "arguments": { ... }
    }
    Do not call the tool. Do not explain. Do not include user data like portfolio or transactions.
"""

TOOLS = {"get_xirr": xirr_tool}


class PFAnalyzerAgent:
    def __init__(self, llm_service, session_id):
        self.llm_service = llm_service
        self.session_id = session_id

    def get_portfolio_summary(self):
        session_data = session_service.get_session_data(self.session_id)
        holdings = {
            "curr_holdings": session_data["curr_holdings"],
            "past_holdings": session_data["past_holdings"],
        }
        messages = [
            {"role": "system", "content": PORTFOLIO_SUMMARY_PROMPT},
            {
                "role": "user",
                "content": f"Here are my holdings:\n```json\n{json.dumps(holdings, indent=2)}\n```",
            },
        ]
        llm_reply, _ = self.llm_service.ask(messages)
        return llm_reply

    async def answer_pf_query(self, pf_query, portfolio):
        messages = [
            {"role": "system", "content": PORTFOLIO_QUERY_PROMPT},
            {"role": "user", "content": pf_query},
        ]
        tool_decision = None  # self.llm_service.ask(messages)
        answer = self.process_tool_call(tool_decision, portfolio)
        return answer

    def process_tool_call(self, tool_decision, portfolio):
        parsed = json.loads(tool_decision)

        tool_name = parsed["tool_name"]
        arguments = parsed["arguments"]
        if "tool_name" == "get_xirr":
            arguments["transactions"] = portfolio["transactions"]
        elif tool_name == "get_cap_composition":
            arguments["holdings"] = portfolio["holdings"]

        result = TOOLS[tool_name](**arguments)
