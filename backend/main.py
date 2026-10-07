"""Campus Customs API — the app you run with:

    uvicorn main:app --reload --port 8000

from inside the backend/ folder. It serves the product catalogue and images,
handles account creation and login, and exposes the chat route that drives the
website's chat widget through the Pydantic AI shop agent.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded
from pydantic_ai.usage import UsageLimits

import audit
import catalogue
import history
import sizing
from agent import get_agent
from config import (
    CHAT_MODE,
    CORS_ORIGINS,
    MODEL_NAME,
    PORTKEY_BASE_URL,
    PRODUCT_IMAGE_DIR,
    get_api_key,
)
from db import ensure_phone_column
from deps import ChatDeps
from models import (
    ChatRequest,
    ChatResponse,
    SizeChartRow,
    SizeRecommendation,
    SizeRecommendationRequest,
    StoredMessage,
)
from routers import auth, products

app = FastAPI(title="Campus Customs API")

STUB_REPLY = (
    "Thanks for the message. The shop assistant is running in offline mode "
    "right now, so this is a placeholder reply. Browse the Products page in "
    "the meantime."
)

# Bound each chat so a misbehaving prompt cannot trigger a runaway, expensive
# loop of model/tool calls. A normal answer needs only a few tool calls.
CHAT_USAGE_LIMITS = UsageLimits(request_limit=6, tool_calls_limit=8)


@app.on_event("startup")
def _startup() -> None:
    # Add the optional users.phone column once, if the seeded DB lacks it.
    ensure_phone_column()


# --- error handling -------------------------------------------------------

_SENSITIVE_FIELDS = {"password", "confirm_password"}


@app.exception_handler(RequestValidationError)
async def _redact_validation_errors(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return validation errors without echoing password values.

    FastAPI's default handler includes the offending input in the response, so
    a mistyped password would be reflected back (and logged). Strip the input
    and any non-serialisable context.
    """

    def _jsonable(value: object) -> bool:
        return isinstance(value, (str, int, float, bool, type(None)))

    cleaned = []
    for error in exc.errors():
        item = {
            k: v
            for k, v in error.items()
            if k != "input" and _jsonable(v) or k in ("loc", "type", "msg")
        }
        ctx = error.get("ctx")
        if isinstance(ctx, dict):
            safe_ctx = {k: v for k, v in ctx.items() if k != "input" and _jsonable(v)}
            if safe_ctx:
                item["ctx"] = safe_ctx
        loc = error.get("loc", ())
        if any(field in _SENSITIVE_FIELDS for field in loc):
            item["msg"] = "Invalid password."
        cleaned.append(item)
    return JSONResponse(status_code=422, content={"detail": cleaned})


# --- middleware and sub-routers ------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(auth.router)

# Product photographs, served straight from the dataset.
if PRODUCT_IMAGE_DIR.is_dir():
    app.mount("/images", StaticFiles(directory=PRODUCT_IMAGE_DIR), name="images")


# --- chat route (drives the website's chat widget) -----------------------


@app.get("/api/chat/history", response_model=list[StoredMessage], tags=["chat"])
async def chat_history(user_id: int, email: str) -> list[StoredMessage]:
    """Return a returning shopper's saved conversation.

    Requires the id and email to match a real user; guests have no history.
    """
    customer = history.resolve_customer(user_id, email)
    if customer is None:
        return []
    return history.load_history(customer["id"])


@app.post("/api/chat", response_model=ChatResponse, tags=["chat"])
async def chat(request: ChatRequest) -> ChatResponse:
    """Send a shopper's message to the shop agent and return its reply.

    For a verified logged-in shopper, past turns are replayed to the agent and
    this exchange is saved. Guests chat normally but nothing is persisted. With
    CHAT_MODE=stub (offline), returns a canned reply and calls no model.
    """
    if CHAT_MODE == "stub":
        return ChatResponse(reply=STUB_REPLY, stub=True)

    try:
        agent = get_agent()
    except RuntimeError as exc:
        # Missing API key is a server configuration problem, not a bad request.
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    # Identify the shopper (if logged in) and build the agent's dependencies.
    customer = history.resolve_customer(request.user_id, request.email)
    deps = ChatDeps(
        user_id=customer["id"] if customer else None,
        first_name=customer["first_name"] if customer else None,
        email=customer["email"] if customer else None,
        current_product_id=request.current_product_id,
    )

    # Returning customers get their past conversation replayed as memory.
    message_history = (
        history.load_history_as_messages(deps.user_id) if deps.is_logged_in else None
    )

    try:
        result = await agent.run(
            request.message,
            deps=deps,
            message_history=message_history,
            usage_limits=CHAT_USAGE_LIMITS,
        )
    except UsageLimitExceeded as exc:
        # The run hit its bounded budget — degrade gracefully instead of paying
        # for an unbounded loop.
        audit.record_event("usage_limit_exceeded")
        raise HTTPException(
            status_code=503,
            detail="That took more work than expected. Please try rephrasing.",
        ) from exc
    except ModelHTTPError as exc:
        # The gateway's content filter rejects some prompts (e.g. injection or
        # abuse attempts) with a 400. That is a safe outcome, not an outage —
        # answer with a calm refusal so the widget keeps working.
        if exc.status_code == 400:
            audit.record_event("content_filtered")
            return ChatResponse(
                reply=(
                    "I can't help with that. I'm here for Campus Customs "
                    "shopping — tell me what you're looking for and I'll find it."
                ),
                stub=False,
            )
        audit.record_event("model_http_error", note=str(exc.status_code))
        raise HTTPException(
            status_code=502, detail="The shop assistant is unavailable right now."
        ) from exc
    except Exception as exc:  # keep the website responsive on other errors
        audit.record_event("error", note=type(exc).__name__)
        raise HTTPException(
            status_code=502, detail="The shop assistant is unavailable right now."
        ) from exc

    # Append-only audit of the loop: every tool call plus the stop reason.
    audit.record_run(result, str(getattr(result.response, "finish_reason", "stop")))

    reply = result.output
    # Ground the cards against the database: drop any invented product and
    # rebuild every card from real catalogue data, so no fabricated price or
    # image can reach the shopper.
    products = catalogue.ground_cards(reply.products)

    # Persist this exchange for logged-in shoppers only.
    if deps.is_logged_in and deps.user_id is not None:
        history.append_exchange(
            deps.user_id, request.message, reply.message, products
        )

    return ChatResponse(reply=reply.message, products=products, stub=False)


# --- health ---------------------------------------------------------------


@app.get("/api/size-guide", response_model=list[SizeChartRow], tags=["sizing"])
async def size_guide() -> list[SizeChartRow]:
    """The unisex size chart: US/UK labels with chest in inches and cm."""
    return [SizeChartRow(**row) for row in sizing.chart()]


@app.post("/api/size-recommendation", response_model=SizeRecommendation, tags=["sizing"])
async def size_recommendation(request: SizeRecommendationRequest) -> SizeRecommendation:
    """Recommend a size from height and weight (metric or imperial)."""
    result = sizing.recommend(request.height, request.weight, request.units)
    return SizeRecommendation(**result)


@app.get("/api/health")
async def health() -> dict[str, object]:
    """Liveness check. Reports whether the key is present, never its value."""
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "gateway": PORTKEY_BASE_URL,
        "chat_mode": CHAT_MODE,
        "api_key_configured": get_api_key() is not None,
        "images_mounted": PRODUCT_IMAGE_DIR.is_dir(),
    }
