import json
import uuid
import datetime as dt
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.models import (
    ChatSession, ChatMessage, PendingAction,
    BookCopy, BorrowRecord,
    MessageRole, ActionType, ActionStatus,
)
from app.chat.schemas import GraphState
from app.chat.agent import agent
from app.chat.tools import AgentDeps

HISTORY_WINDOW = 20          # last N messages loaded into context
SESSION_REUSE_MINUTES = 120  # reuse session if updated_at within this window


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_confirm(text: str) -> bool:
    keywords = {"yes", "yeah", "sure", "ok", "okay", "proceed", "go ahead", "confirm", "do it", "yep"}
    return any(k in text.lower() for k in keywords)


def _is_cancel(text: str) -> bool:
    keywords = {"no", "cancel", "stop", "abort", "nevermind", "never mind", "nope", "don't"}
    return any(k in text.lower() for k in keywords)


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

async def load_session(state: GraphState, db: AsyncSession) -> GraphState:
    user_id = state["user_id"]
    token = state.get("session_token")

    session = None

    if token:
        result = await db.execute(
            select(ChatSession).where(ChatSession.session_token == token)
        )
        session = result.scalar_one_or_none()

    # For members: reuse if within window, else create new
    if session and user_id:
        cutoff = datetime.now(dt.UTC) - dt.timedelta(minutes=SESSION_REUSE_MINUTES)
        if session.updated_at < cutoff:
            session = None

    if not session:
        session = ChatSession(
            session_token=str(uuid.uuid4()),
            user_id=user_id,
        )
        db.add(session)
        await db.flush()

    # Load last N messages as LangChain message objects
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.sequence_number.desc())
        .limit(HISTORY_WINDOW)
    )
    rows = result.scalars().all()
    rows = list(reversed(rows))

    history = []
    for row in rows:
        if row.role == MessageRole.user:
            history.append(HumanMessage(content=row.content))
        elif row.role == MessageRole.assistant:
            history.append(AIMessage(content=row.content))

    return {
        **state,
        "session_id": session.id,
        "session_token": session.session_token,
        "messages": history,
    }


async def check_pending(state: GraphState, db: AsyncSession) -> GraphState:
    result = await db.execute(
        select(PendingAction).where(
            and_(
                PendingAction.session_id == state["session_id"],
                PendingAction.status == ActionStatus.pending,
            )
        )
    )
    pending = result.scalar_one_or_none()

    if pending:
        payload = json.loads(pending.action_payload)
        return {
            **state,
            "pending_action_id": pending.id,
            "pending_action_type": pending.action_type.value,
            "pending_action_payload": payload,
        }

    return {
        **state,
        "pending_action_id": None,
        "pending_action_type": None,
        "pending_action_payload": None,
    }


async def resolve_pending(state: GraphState, db: AsyncSession) -> GraphState:
    user_message = state["user_message"]
    action_id = state["pending_action_id"]
    action_type = state["pending_action_type"]
    payload = state["pending_action_payload"]

    if _is_confirm(user_message):
        if action_type == "borrow":
            copy_id = payload["book_copy_id"]
            record = BorrowRecord(
                book_copy_id=copy_id,
                user_id=state["user_id"],
            )
            db.add(record)
            await db.execute(
                update(BookCopy).where(BookCopy.id == copy_id).values(availability=False)
            )
            reply = f"Done! I've borrowed **{payload['title']}** for you."

        elif action_type == "return":
            record_id = payload["borrow_record_id"]
            copy_id = payload["book_copy_id"]
            await db.execute(
                update(BorrowRecord)
                .where(BorrowRecord.id == record_id)
                .values(return_date=datetime.now(dt.UTC))
            )
            await db.execute(
                update(BookCopy).where(BookCopy.id == copy_id).values(availability=True)
            )
            reply = f"Done! **{payload['title']}** has been returned."

        else:
            reply = "Action completed."

        await db.execute(
            update(PendingAction)
            .where(PendingAction.id == action_id)
            .values(status=ActionStatus.executed, resolved_at=datetime.now(dt.UTC))
        )

    elif _is_cancel(user_message):
        await db.execute(
            update(PendingAction)
            .where(PendingAction.id == action_id)
            .values(status=ActionStatus.cancelled, resolved_at=datetime.now(dt.UTC))
        )
        reply = "No problem, I've cancelled that for you."

    else:
        reply = (
            f"I need a yes or no — shall I go ahead with "
            f"**{payload.get('title', 'this action')}**?"
        )

    return {**state, "assistant_reply": reply}


async def run_agent(state: GraphState, db: AsyncSession) -> GraphState:
    deps = AgentDeps(db=db, user_id=state["user_id"])

    history = state.get("messages", [])
    current = HumanMessage(content=state["user_message"])
    all_messages = history + [current]

    result = await agent.run(
        state["user_message"],
        message_history=history,
        deps=deps,
    )

    reply = result.output

    # Detect if any staged tool was called
    staged_type = None
    staged_payload = None

    for msg in result.all_messages():
        for part in getattr(msg, "parts", []):
            tool_name = getattr(part, "tool_name", None)
            tool_return = getattr(part, "content", None)

            if tool_name == "stage_borrow_intent" and tool_return:
                staged_type = "borrow"
                staged_payload = (
                    json.loads(tool_return) if isinstance(tool_return, str)
                    else tool_return
                )
            elif tool_name == "stage_return_intent" and tool_return:
                staged_type = "return"
                staged_payload = (
                    json.loads(tool_return) if isinstance(tool_return, str)
                    else tool_return
                )

    return {
        **state,
        "assistant_reply": reply,
        "staged_action_type": staged_type,
        "staged_action_payload": staged_payload,
    }


async def write_pending_action(state: GraphState, db: AsyncSession) -> GraphState:
    # Cancel any existing pending action first
    await db.execute(
        update(PendingAction)
        .where(
            and_(
                PendingAction.session_id == state["session_id"],
                PendingAction.status == ActionStatus.pending,
            )
        )
        .values(status=ActionStatus.cancelled, resolved_at=datetime.now(dt.UTC))
    )

    action = PendingAction(
        session_id=state["session_id"],
        user_id=state["user_id"],
        action_type=ActionType.borrow if state["staged_action_type"] == "borrow" else ActionType.return_,
        status=ActionStatus.pending,
        action_payload=json.dumps(state["staged_action_payload"]),
    )
    db.add(action)
    await db.flush()

    return state


async def save_and_end(state: GraphState, db: AsyncSession) -> GraphState:
    session_id = state["session_id"]

    # Get next sequence number
    result = await db.execute(
        select(ChatMessage.sequence_number)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.sequence_number.desc())
        .limit(1)
    )
    last_seq = result.scalar_one_or_none() or 0

    user_msg = ChatMessage(
        session_id=session_id,
        role=MessageRole.user,
        content=state["user_message"],
        sequence_number=last_seq + 1,
    )
    assistant_msg = ChatMessage(
        session_id=session_id,
        role=MessageRole.assistant,
        content=state["assistant_reply"],
        sequence_number=last_seq + 2,
    )
    db.add(user_msg)
    db.add(assistant_msg)

    await db.execute(
        update(ChatSession)
        .where(ChatSession.id == session_id)
        .values(updated_at=datetime.now(dt.UTC))
    )

    await db.commit()
    return state


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def route_after_check_pending(state: GraphState) -> str:
    if state.get("pending_action_id"):
        return "resolve_pending"
    return "run_agent"


def route_after_run_agent(state: GraphState) -> str:
    if state.get("staged_action_type"):
        return "write_pending_action"
    return "save_and_end"


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph(db: AsyncSession):
    builder = StateGraph(GraphState)

    async def _load_session(s):       return await load_session(s, db)
    async def _check_pending(s):      return await check_pending(s, db)
    async def _resolve_pending(s):    return await resolve_pending(s, db)
    async def _run_agent(s):          return await run_agent(s, db)
    async def _write_pending(s):      return await write_pending_action(s, db)
    async def _save_and_end(s):       return await save_and_end(s, db)

    builder.add_node("load_session",         _load_session)
    builder.add_node("check_pending",        _check_pending)
    builder.add_node("resolve_pending",      _resolve_pending)
    builder.add_node("run_agent",            _run_agent)
    builder.add_node("write_pending_action", _write_pending)
    builder.add_node("save_and_end",         _save_and_end)

    builder.set_entry_point("load_session")

    builder.add_edge("load_session", "check_pending")
    builder.add_conditional_edges("check_pending", route_after_check_pending)
    builder.add_edge("resolve_pending", "save_and_end")
    builder.add_conditional_edges("run_agent", route_after_run_agent)
    builder.add_edge("write_pending_action", "save_and_end")
    builder.add_edge("save_and_end", END)

    return builder.compile()