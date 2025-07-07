import json
from typing import List, Optional


from services.openai_service import OpenAIService
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
    You are an intelligent assistant that solves user queries by reasoning through steps and using tools when necessary.

    You follow the ReAct (Reasoning + Acting) process:

    1. Thought - Reflect on what needs to be done.
    2. Action - Choose a tool and provide inputs in JSON format.
    3. Observation - Process the tool's result (you'll receive this from the system).
    4. Repeat - Continue reasoning and calling tools as needed, or provide the final answer.

    ---

    Available tools:
    - get_xirr(transactions: List[Dict]) — Calculate annualized return based on dated cashflows.
    - get_total_return(data_key: str) — Compute absolute gain/loss from portfolio.
    - get_cap_composition(data_key: str) — Show portfolio split by asset type (equity, debt, etc.).

    ---

    Response format rules:

    If a tool is needed:
    Thought: I need to calculate the XIRR for the user's mutual fund.
    Action: get_xirr
    Action Input:
    {
        "transactions": "var_abc123"
    }

    If you receive a tool result:
    Observation: The XIRR is 11.2%
    Thought: Now I can give the final answer.
    Answer: The annualized return on your portfolio is 11.2%.

    Always follow this structure
    Do not execute tools yourself
    Do not include large data — use references like var_abc123
    Stop with Answer: only when you have the final user-facing response
"""

# TOOLS = {"get_xirr": xirr_tool}


class PFAnalyzerAgent:
    def __init__(
        self, session_id: str, llm: OpenAIService, tools: Optional[List] = None
    ):
        self.llm = llm
        self.tools = tools
        self.session_id = session_id
        self.fetch_session_data()

    def fetch_session_data(self):
        session_data = session_service.get_session_data(self.session_id)
        self.curr_holdings = session_data["curr_holdings"]
        self.past_holdings = session_data["past_holdings"]
        self.txns = session_data["txns"]

        holdings = {
            "curr_holdings": self.curr_holdings,
            "past_holdings": self.past_holdings,
        }

        self.holdings_as_json_str = f"```json\n{json.dumps(holdings, indent=2)}\n```"

    def get_portfolio_summary(self):
        messages = [
            {"role": "system", "content": PORTFOLIO_SUMMARY_PROMPT},
            {
                "role": "user",
                "content": f"Here are my holdings:\n{self.holdings_as_json_str}",
            },
        ]
        llm_reply, _ = self.llm.ask(messages)
        return llm_reply

    async def answer_pf_query(self, pf_query):
        messages = [
            {"role": "system", "content": PORTFOLIO_QUERY_PROMPT},
            {
                "role": "user",
                "content": f"Here are my holdings:\n{self.holdings_as_json_str}",
            },
            {
                "role": "user",
                "content": "I have curr_holdings, past_holdings and txns variables initialised. You can send them as arguments.",
            },
            {"role": "user", "content": pf_query},
        ]
        final_answer = "Sorry! Unable answer to your query."
        while True:
            final_answer, tool_calls = self.llm.ask(messages, self.tools)
            if final_answer:
                return final_answer
            elif tool_calls:
                for tool_call in tool_calls:
                    observation = self.process_tool_call(tool_call)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": observation,
                        }
                    )
            else:
                break
        return final_answer

    def process_tool_call(self, tool_call):
        parsed = json.loads(tool_call)

        tool_name = parsed["tool_name"]
        arguments = parsed["arguments"]
        if "tool_name" == "get_xirr":
            pass
        elif tool_name == "get_cap_composition":
            arguments["holdings"] = portfolio["holdings"]

        result = TOOLS[tool_name](**arguments)
