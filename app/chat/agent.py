from pydantic_ai import Agent
from app.config.chat_model import get_model
from app.chat.tools import (
    AgentDeps,
    search_books,
    check_availability,
    stage_borrow_intent,
    stage_return_intent,
    get_active_borrows,
)

SYSTEM_PROMPT = """
You are a helpful library assistant for a Library Management System.

You help users:
- Search for books by title, author, or topic
- Check book availability
- Borrow books (members only)
- Return books (members only)
- View their active borrows (members only)

Guidelines:
- Always search for books before checking availability or staging a borrow/return.
- Never call stage_borrow_intent or stage_return_intent for guests (user_id is None).
- If a guest tries to borrow or return, politely tell them to log in.
- When staging a borrow or return, always confirm the action with the user before proceeding.
- Be concise and friendly.
- If a tool raises an error, relay the message naturally to the user.
"""

agent = Agent(
    model=get_model(),
    deps_type=AgentDeps,
    system_prompt=SYSTEM_PROMPT,
    tools=[
        search_books,
        check_availability,
        stage_borrow_intent,
        stage_return_intent,
        get_active_borrows,
    ],
)