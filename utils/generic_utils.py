import re
import json


def extract_raw_json(response: str):
    match = re.search(r"\{.*\}", response, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found")
    return json.loads(match.group(0))


def object_to_json_str(obj):
    return f"```json{json.dumps(obj, indent=2)}```"
