import json
from typing import List, Optional


from app_context import session_service
from services.openai_service import OpenAIService
from tools.xirr_tool import get_xirr

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
    You are an intelligent assistant that answers user questions about their investment portfolio by reasoning through steps and calling functions when needed.

    You have access to a set of tools (functions). Use them when appropriate to obtain the information required to answer the user's query.

    Your job is to:
    - Understand the user’s query
    - Call the most appropriate function with the correct arguments
    - Wait for the result of that function call (you will receive it from the system)
    - Continue reasoning or call more functions if needed
    - Return a final answer to the user once sufficient information is available

    ---

    Available functions:
    - get_xirr(cashflows: List[Dict]) — Calculate annualized return based on dated cashflows.

    ---

    Guidelines:
    - Use tool calls only when required — not every query needs a tool.
    - The system will handle calling the tool — just provide the function name and arguments.
    - Once you have all the information you need, respond to the user with a clear and final answer.
    - Do not include any internal reasoning, thoughts, or tool call descriptions in your response.

    Only respond with a natural user-facing answer when you are done.
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
        self.cashflows = session_data["cashflows"]

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
        llm_reply, _ = self.llm.invoke(messages)
        return llm_reply

    async def ask(self, query):
        messages = [
            {"role": "system", "content": PORTFOLIO_QUERY_PROMPT},
            {
                "role": "user",
                "content": (
                    "I have initialized the following data variables for you:\n"
                    "- `var_txns`: all my transactions\n"
                    "- `var_cashflows`: signed cashflows for XIRR calculation\n"
                    "- `var_curr_holdings`: current holdings\n"
                    "- `var_past_holdings`: holdings sold in the past\n\n"
                    "You can refer to these variables in function calls — do not generate or assume any actual data.\n\n"
                    f"My full holdings snapshot (for your context only, not for tool input):\n{self.holdings_as_json_str}\n\n"
                    f"Here is my question:\n{query}"
                ),
            },
            # {"role": "user", "content": query},
        ]
        final_answer = "Sorry! Unable answer to your query."
        while True:
            final_answer, tool_calls = self.llm.invoke(messages, self.tools)
            if final_answer:
                return final_answer
            elif tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "tool_calls": [
                            tool_call.model_dump() for tool_call in tool_calls
                        ],  # type: ignore
                    }
                )
                for tool_call in tool_calls:
                    observation = str(self.process_tool_call(tool_call))
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": observation,
                        }
                    )
            else:
                break
        return final_answer

    def process_tool_call(self, tool_call):
        tool_name, arguments = self.llm.parse_tool_call(tool_call)

        if tool_name == "get_xirr":
            if arguments["cashflows"] == "var_cashflows":
                return get_xirr(self.cashflows)
        # elif tool_name == "get_cap_composition":
        #     arguments["holdings"] = portfolio["holdings"]

        # result = TOOLS[tool_name](**arguments)
