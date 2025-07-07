# api/chat.py
from io import BytesIO
from fastapi import APIRouter, File, Form, Request, UploadFile
from pydantic import BaseModel

from agents.pf_analyzer_agent import PFAnalyzerAgent
from app_context import session_service, llm
from domain.cas_parser import CasParser
from tools.schema import tools

router = APIRouter(prefix="/api", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = None


@router.post("/chat")
async def chat_endpoint(request: Request):
    body = await request.json()
    user_query = body.get("message")

    session_id = request.headers.get("session_id")
    pf_agent = PFAnalyzerAgent(session_id, llm, tools)

    reply = await pf_agent.answer_pf_query(user_query)
    return {"reply": reply}


@router.post("/upload")
async def upload_file(
    request: Request, file: UploadFile = File(...), password: str = Form(...)
):
    file_bytes = await file.read()
    file_stream = BytesIO(file_bytes)

    cas_parser = CasParser(file_stream, password)
    curr_holdings, past_holdings, txns = cas_parser.parse()

    session_id = request.headers.get("session_id")
    session_data = {
        "curr_holdings": curr_holdings,
        "past_holdings": past_holdings,
        "txns": txns,
    }
    session_service.set_session_data(session_id, session_data)

    pf_agent = PFAnalyzerAgent(session_id, llm)
    summary = pf_agent.get_portfolio_summary()
    print(summary)
    return {"reply": summary}
