import json
import os
from typing import List
from openai import OpenAI


class OpenAIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.llm_client = OpenAI(api_key=api_key)

    def set_tool_schemas(self, tool_schemas):
        self.tool_schemas = tool_schemas

    def ask(self, messages: List):
        response = self.llm_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            # tools=self.tool_schemas,
            # tool_choice="auto",
        )
        return response

    def parse_tool_call(self, tool_call):
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        return func_name, args

    def parse_response(self, response):
        message = response.choices[0].message

        tool_call, llm_reply = None, ""
        if message.tool_calls:
            tool_call = message.tool_calls[0]
        else:
            llm_reply = response.choices[0].message.content

        return llm_reply, tool_call
