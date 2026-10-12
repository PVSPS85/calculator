"""Chat routing and request validation for CalcAI conversational assistant."""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.services.gemini_service import gemini_service, GeminiServiceException

router = APIRouter(tags=["AI Chat"])


class ChatRequest(BaseModel):
    """Incoming chat message request payload."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User text query or prompt",
    )
    session_id: Optional[str] = Field(
        None,
        max_length=64,
        description="Unique session identifier for conversation continuity",
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata such as math expression and result",
    )


class ChatResponse(BaseModel):
    """Outgoing chat response payload."""
    reply: str
    session_id: str
    model: str


@router.post("/chat", response_model=ChatResponse)
def handle_chat_message(request: ChatRequest):
    """Process user prompt and return Gemini AI response."""
    try:
        reply_text, session_id, model_name = gemini_service.send_message(
            message=request.message,
            session_id=request.session_id,
            context=request.context,
        )
        return ChatResponse(
            reply=reply_text,
            session_id=session_id,
            model=model_name,
        )
    except GeminiServiceException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred: {str(e)}",
        )
