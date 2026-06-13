from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config.database import get_db
from app.chat.schemas import ChatRequest, ChatResponse, GraphState
from app.chat.graph import build_graph
from app.chat.dependencies import get_optional_user_id
from app.config.models import ChatMessage, ChatSession

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user_id: int | None = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db),
):
    initial_state: GraphState = {
        "session_id": 0,
        "session_token": request.session_token or "",
        "user_id": user_id,
        "user_message": request.message,
        "assistant_reply": "",
        "pending_action_id": None,
        "pending_action_type": None,
        "pending_action_payload": None,
        "staged_action_type": None,
        "staged_action_payload": None,
        "messages": [],
    }

    graph = build_graph(db)
    final_state = await graph.ainvoke(initial_state)

    return ChatResponse(
        reply=final_state["assistant_reply"],
        session_token=final_state["session_token"],
    )


@router.get("/history", response_model=list[dict])
async def get_history(
    session_token: str,
    user_id: int | None = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).where(ChatSession.session_token == session_token)
    )
    session = result.scalar_one_or_none()

    if not session:
        return []

    # Members can only see their own sessions
    if user_id and session.user_id and session.user_id != user_id:
        return []

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.sequence_number)
    )
    messages = result.scalars().all()

    return [
        {
            "role": msg.role.value,
            "content": msg.content,
            "sequence_number": msg.sequence_number,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in messages
    ]