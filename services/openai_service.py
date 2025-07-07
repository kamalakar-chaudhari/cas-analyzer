import json
import os
from typing import Dict, List, Optional
from openai import OpenAI


class OpenAIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.llm_client = OpenAI(api_key=api_key)

    def ask(self, messages: List[Dict], tools: Optional[List] = None):
        response = self.llm_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools or [],
            tool_choice="auto",
        )
        llm_reply, tool_calls = self.parse_response(response)
        return llm_reply, tool_calls

    def parse_tool_call(self, tool_call):
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        return func_name, args

    def parse_response(self, response):
        message = response.choices[0].message

        tool_calls, llm_reply = None, ""
        if message.tool_calls:
            tool_calls = message.tool_calls
        else:
            llm_reply = response.choices[0].message.content

        return llm_reply, tool_calls
