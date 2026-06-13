from pydantic import BaseModel
from langgraph.graph import MessagesState

class GraphState(MessagesState):
    session_id: int
    session_token: str
    user_id: int | None
    user_message: str
    assistant_reply: str
    pending_action_id: int | None
    pending_action_type: str | None      # "borrow" | "return"
    pending_action_payload: dict | None
    staged_action_type: str | None       # set by tools, detected in run_agent
    staged_action_payload: dict | None


# --- HTTP request / response ---

class ChatRequest(BaseModel):
    message: str
    session_token: str | None = None     # None = start new session


class ChatResponse(BaseModel):
    reply: str
    session_token: str


# --- Tool output schemas ---

class BookSearchResult(BaseModel):
    id: int
    title: str
    author: str | None
    description: str | None
    copies_available: int


class AvailabilityResult(BaseModel):
    book_id: int
    title: str
    copies_available: int
    next_copy_id: int | None             # None if no copies available


class BorrowIntentPayload(BaseModel):
    book_id: int
    book_copy_id: int
    title: str


class ReturnIntentPayload(BaseModel):
    borrow_record_id: int
    book_copy_id: int
    title: str


class ActiveBorrow(BaseModel):
    borrow_record_id: int
    book_copy_id: int
    title: str
    borrow_date: str
    due_date: str