# api/chat.py
import os
from io import BytesIO

from fastapi import APIRouter, File, Form, Request, UploadFile

from agents.pf_analyzer_agent import PFAnalyzerAgent
from agents.pf_analyzer_graph import PFAnalyzerGraphAgent
from config.app_context import cas_etl_workflow, llm
from tools.schema import tools

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat")
async def chat_endpoint(request: Request):
    body = await request.json()
    user_query = body.get("message")

    reply = ""
    if os.getenv("USE_LANGGRAPH_AGENT"):
        session_id = request.headers.get("session_id")
        pf_agent = PFAnalyzerGraphAgent(session_id, llm, tools)
        reply = await pf_agent.ask(user_query)
    else:
        session_id = request.headers.get("session_id")
        pf_agent = PFAnalyzerAgent(session_id, llm, tools)
        reply = await pf_agent.ask(user_query)
    return {"reply": reply}


@router.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...), password: str = Form(...)):
    file_bytes = await file.read()
    file_stream = BytesIO(file_bytes)

    session_id = request.headers.get("session_id")
    pf_summary = cas_etl_workflow.invoke(session_id, file_stream, password)
    return {"reply": pf_summary}
