# api/chat.py
from fastapi import APIRouter, File, Form, Request, UploadFile
from pydantic import BaseModel

from app_context import cas_parser_agent, pf_analyzer_agent

router = APIRouter(prefix="/api", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = None


@router.post("/chat")
async def chat_endpoint(request: Request):
    user_query = await request.json().get("message")
    reply = await pf_analyzer_agent.answer(user_query)
    return {"reply": reply}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), password: str = Form(...)):
    portfolio = await cas_parser_agent.get_portfolio_from_pdf(file, password)
    return {"reply": portfolio}
