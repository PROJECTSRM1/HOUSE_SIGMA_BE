from fastapi import APIRouter, HTTPException # pyright: ignore[reportMissingImports]
from pydantic import BaseModel # pyright: ignore[reportMissingImports]
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import logging
from groq import Groq # pyright: ignore[reportMissingImports]
import markdown # pyright: ignore[reportMissingModuleSource]
import os

from utils.prompt import SYSTEM_PROMPT, get_real_estate_context

router = APIRouter(prefix="/api/chat")

# In-memory session store
chat_sessions = {}

# Groq Client
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

# ------------------------
# MARKDOWN FORMATTER
# ------------------------
def format_markdown_to_html(text: str) -> str:
    """
    Convert Markdown text from LLM into safe HTML
    for clean UI rendering on the frontend.
    """
    return markdown.markdown(text, extensions=["extra"])


# ------------------------
# MODELS
# ------------------------
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime = datetime.now(timezone.utc)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str          # raw markdown text
    response_html: str     # converted HTML version
    session_id: str


logger = logging.getLogger("chat-router")

# ------------------------
# CHAT ENDPOINT
# ------------------------
@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())

        # Create new session if not exists
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []

        # Add user message
        user_msg = ChatMessage(role="user", content=request.message)
        chat_sessions[session_id].append(user_msg.dict())

        # Prepare messages for Groq
        messages = [{
            "role": "system",
            "content": SYSTEM_PROMPT + get_real_estate_context()
        }]

        for msg in chat_sessions[session_id][-10:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Groq API call
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )

        assistant_reply = completion.choices[0].message.content

        # Convert Markdown → HTML
        assistant_reply_html = format_markdown_to_html(assistant_reply)

        # Save assistant message
        assistant_msg = ChatMessage(role="assistant", content=assistant_reply)
        chat_sessions[session_id].append(assistant_msg.dict())

        return ChatResponse(
            response=assistant_reply,
            response_html=assistant_reply_html,
            session_id=session_id
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------
# CHAT HISTORY ENDPOINT
# ------------------------
@router.get("/history/{session_id}")
async def get_history(session_id: str):
    return {
        "session_id": session_id,
        "messages": chat_sessions.get(session_id, [])
    }


# ------------------------
# CLEAR SESSION
# ------------------------
@router.delete("/clear/{session_id}")
async def clear_history(session_id: str):
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        return {"message": "Session cleared"}

    return {"message": "Session not found"}
