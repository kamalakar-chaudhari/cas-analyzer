import json

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph
from langgraph.prebuilt import tools_condition

from services.openai_service import OpenAIService
from tools.cap_composition_tool import get_asset_class_summary
from tools.filter_transactions_tool import filter_transactions_by_isin
from tools.schema import tools
from tools.xirr_tool import get_xirr
from types_ import CASAgentState
from utils.db_utils import get_sqlite_connection
from utils.generic_utils import object_to_json_str

PORTFOLIO_QUERY_PROMPT = """
You are an intelligent assistant that answers user questions about their investment portfolio
by reasoning through steps and calling tools (functions) when needed.

You have access to a set of tools. Use them when required to obtain information needed
to answer the user's query.

Your responsibilities:
- Understand the user's query
- Call the most appropriate function with correct arguments (when needed)
- Wait for the system to return the result
- Continue reasoning or call more tools if needed
- Once you have all necessary information, return a final, clear answer to the user

Data Variables Available:
- 'var_transactions': all my transactions
- 'var_curr_holdings': current holdings
- 'var_past_holdings': holdings sold in the past

You can reference these variables in tool calls. Do not generate or assume any actual data.

---

Guidelines:
- Use tool calls only when necessary. Not all queries require them.
- To call a tool, respond with the function name and a JSON object of arguments. Do not explain the call.
- Once done, respond with a final natural answer — concise and accurate.
- If a chart would help, return a valid Python code snippet using matplotlib or plotly that can be used in Streamlit.
- Never include reasoning, internal thoughts, or tool descriptions in the final response.
- If the required information is missing or unknown, say so honestly — do not fabricate data.
"""


class PFAnalyzerAgent_:
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
            {"role": "system", "content": PORTFOLIO_QUERY_PROMPT},
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
                    "- var_transactions: all my transactions\n"
                    "- var_curr_holdings: current holdings\n"
                    "- var_past_holdings: holdings sold in the past\n\n"
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


# --------------------

llm_with_tools = ChatOpenAI(
    temperature=0,
    model="gpt-4o",
).bind_tools(tools, tool_choice="auto", strict=False)


def llm_node(state: CASAgentState):
    resp = llm_with_tools.invoke(state["messages"])
    return {"messages": state["messages"] + [resp]}


tools_by_name = {tool.name: tool for tool in tools}


def tool_node(state: dict):
    def _parse_tool_call(tool_call):
        tool = tools_by_name[tool_call["name"]]
        args = tool_call["args"]
        if args["transactions"] == "var_transactions":
            args["transactions"] = state.get("transactions")
        return tool, args

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool, args = _parse_tool_call(tool_call)
        observation = tool.invoke(args)

        result.append(
            ToolMessage(content=object_to_json_str(observation), tool_call_id=tool_call["id"])
        )
    return {"messages": state["messages"] + result}


class PFAnalyzerAgent:
    def __init__(self):
        graph_builder = StateGraph(CASAgentState)
        graph_builder.add_node("llm_node", llm_node)
        graph_builder.add_node("tools", tool_node)

        graph_builder.set_entry_point("llm_node")
        graph_builder.add_conditional_edges("llm_node", tools_condition)
        graph_builder.add_edge("tools", "llm_node")
        graph_builder.set_finish_point("llm_node")

        with get_sqlite_connection() as conn:
            memory = SqliteSaver(conn)
            self.agent = graph_builder.compile(checkpointer=memory)

    def _get_system_prompt(self, state: CASAgentState):
        holdings = {
            "curr_holdings": state["curr_holdings"],
            "past_holdings": state["past_holdings"],
        }

        holdings_as_json_str = f"```json\n{json.dumps(holdings, indent=2)}\n```"

        return [
            SystemMessage(PORTFOLIO_QUERY_PROMPT),
            HumanMessage(f"Here are my holdings:\n{holdings_as_json_str}"),
        ]

    def _filter_tool_messages(self, messages):
        return [msg for msg in messages if msg.type not in {"tool", "tool_use", "tool_result"}]

    def invoke(self, session_id, query):
        config = {"configurable": {"thread_id": session_id}}
        state = self.agent.get_state(config).values
        if not (messages := state["messages"]):
            messages = self._get_system_prompt(state)
        else:
            messages = self._filter_tool_messages(messages)
        messages.append(HumanMessage(query))
        result = self.agent.invoke({"messages": messages}, config=config)
        return result["messages"][-1].content
