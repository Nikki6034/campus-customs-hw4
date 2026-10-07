"""Chat history persistence for logged-in shoppers.

History lives in the dataset's existing `chat_messages` table
(user_id, role, content, products_json, created_at). Only logged-in users'
messages are stored; guests can chat but nothing is written.

Three jobs:
  - resolve_customer: verify a claimed identity against the users table
  - load_history / load_history_as_messages: read a returning shopper's past
    turns, both for the widget and as Pydantic AI message history
  - append_exchange: save a user turn and the assistant's reply
"""

import json

from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from db import connect, connect_rw
from models import ChatProductCard, StoredMessage

# Cap how much past conversation we replay to the model, to bound token cost.
MAX_HISTORY_MESSAGES = 20


def resolve_customer(user_id: int | None, email: str | None) -> dict | None:
    """Return {id, first_name, email} if the id and email match a real user.

    Requiring both to match is a light guard against a client claiming another
    user's id. (A production app would authenticate the request with a session
    token instead; see output/harness.md.)
    """
    if user_id is None or not email:
        return None
    with connect() as conn:
        row = conn.execute(
            "SELECT id, first_name, email FROM users "
            "WHERE id = ? AND LOWER(email) = ?",
            (user_id, email.lower()),
        ).fetchone()
    if row is None:
        return None
    return {"id": row["id"], "first_name": row["first_name"], "email": row["email"]}


def load_history(user_id: int, limit: int = MAX_HISTORY_MESSAGES) -> list[StoredMessage]:
    """Most recent `limit` turns for a user, in chronological order."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT role, content, products_json FROM chat_messages "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()

    messages: list[StoredMessage] = []
    for row in reversed(rows):
        products: list[ChatProductCard] = []
        if row["products_json"]:
            try:
                products = [ChatProductCard(**p) for p in json.loads(row["products_json"])]
            except (json.JSONDecodeError, TypeError, ValueError):
                products = []
        messages.append(
            StoredMessage(role=row["role"], content=row["content"], products=products)
        )
    return messages


def load_history_as_messages(user_id: int, limit: int = MAX_HISTORY_MESSAGES) -> list[ModelMessage]:
    """Past turns rebuilt as Pydantic AI messages, so the agent remembers."""
    history = load_history(user_id, limit)
    messages: list[ModelMessage] = []
    for turn in history:
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=turn.content)]))
    return messages


def append_exchange(
    user_id: int,
    user_message: str,
    assistant_message: str,
    products: list[ChatProductCard],
) -> None:
    """Persist one user turn and the assistant's reply for a logged-in user."""
    products_json = (
        json.dumps([p.model_dump() for p in products]) if products else None
    )
    with connect_rw() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) "
            "VALUES (?, 'user', ?, NULL)",
            (user_id, user_message),
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) "
            "VALUES (?, 'assistant', ?, ?)",
            (user_id, assistant_message, products_json),
        )
        conn.commit()
