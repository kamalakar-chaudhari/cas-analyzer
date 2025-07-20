import json

from services.openai_service import OpenAIService
from tools.cap_composition_tool import get_asset_class_summary
from tools.filter_transactions_tool import filter_transactions_by_isin
from tools.xirr_tool import get_xirr

# from config.app_context import session_service
from utils.generic_utils import object_to_json_str

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
    - Understand the user's query
    - Call the most appropriate function with the correct arguments
    - Wait for the result of that function call (you will receive it from the system)
    - Continue reasoning or call more functions if needed
    - Return a final answer to the user once sufficient information is available

    ---

    Guidelines:
    - Use tool calls only when required — not every query needs a tool.
    - The system will handle calling the tool — just provide the function name and arguments.
    - Once you have all the information you need, respond to the user with a clear and final answer.
    - If the result would benefit from visual representation (e.g., comparing performance across funds), return a code snippet that can be used in Streamlit to render the relevant graph using matplotlib or plotly.
    - Do not include any internal reasoning, thoughts, or tool call descriptions in your response.

    Only respond with a natural user-facing answer when you are done.
"""


class PFAnalyzerAgent:
    def __init__(self, session_id: str, llm: OpenAIService, tools: list | None = None):
        self.llm = llm
        self.tools = tools
        self.session_id = session_id
        self.fetch_session_data()

    def fetch_session_data(self):
        session_data = {}  # session_service.get_session_data(self.session_id)
        self.curr_holdings = session_data["curr_holdings"]
        self.past_holdings = session_data["past_holdings"]
        self.transactions = session_data["transactions"]

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
                    "- `var_transactions`: all my transactions\n"
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
                        "tool_calls": [tool_call.model_dump() for tool_call in tool_calls],  # type: ignore
                    }
                )
                for tool_call in tool_calls:
                    observation = self.process_tool_call(tool_call)
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

    def process_tool_call(self, tool_call) -> str:
        tool_name, arguments = self.llm.parse_tool_call(tool_call)

        if tool_name == "get_xirr":
            if (transactions := arguments["transactions"]) == "var_transactions":
                transactions = self.transactions
            return str(get_xirr(transactions))
        elif tool_name == "filter_transactions_by_isin":
            if (transactions := arguments["transactions"]) == "var_transactions":
                transactions = self.transactions
            return object_to_json_str(filter_transactions_by_isin(transactions, arguments["isin"]))
        elif tool_name == "get_asset_class_summary":
            if (curr_holdings := arguments["curr_holdings"]) == "var_curr_holdings":
                curr_holdings = self.curr_holdings
            return object_to_json_str(get_asset_class_summary(curr_holdings))
