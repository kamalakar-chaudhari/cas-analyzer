import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph
from langgraph.prebuilt import tools_condition

from tools.schema import tools
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

llm_with_tools = ChatOpenAI(
    temperature=0,
    model="gpt-4.1-mini",
).bind_tools(tools, tool_choice="auto", strict=False)


def llm_node(state: CASAgentState):
    resp = llm_with_tools.invoke(state["messages"])
    return {"messages": state["messages"] + [resp]}


tools_by_name = {tool.name: tool for tool in tools}


def tool_node(state: dict):
    def _parse_tool_call(tool_call):
        tool = tools_by_name[tool_call["name"]]
        args = tool_call["args"]
        if args.get("transactions") == "var_transactions":
            args["transactions"] = state.get("transactions")
        if args.get("curr_holdings") == "var_curr_holdings":
            args["curr_holdings"] = state.get("curr_holdings")
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
        return [
            msg
            for msg in messages
            if (
                isinstance(msg, (HumanMessage | AIMessage | SystemMessage))
                and not getattr(msg, "tool_calls", None)  # removes assistant tool calls
            )
        ]
        # return [msg for msg in messages if msg.type not in {"tool", "tool_use", "tool_result"}]

    def invoke(self, session_id, query):
        config = {"configurable": {"thread_id": session_id}}
        state = self.agent.get_state(config).values
        if not (messages := state["messages"]):
            messages = self._get_system_prompt(state)
        else:
            messages = self._filter_tool_messages(messages)
        messages.append(HumanMessage(query))
        result = self.agent.invoke({"messages": messages}, config=config)
        print(result["messages"][-1])
        return result["messages"][-1].content


if __name__ == "__main__":
    graph = PFAnalyzerAgent()
    graph.invoke(
        "c3d8b4e6-0122-4330-9d08-ea31e7035bb0",
        "what is the historical xirr of my current and past schemes?",
    )
    # config = {"configurable": {"thread_id": "c3d8b4e6-0122-4330-9d08-ea31e7035bb0"}}
    # graph.agent.get_state(config)
