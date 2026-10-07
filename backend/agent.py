"""The Campus Customs shop agent (Pydantic AI, behind the Portkey gateway).

Loaded lazily so importing the app never requires a key — the key is only
needed when a chat request actually reaches the agent.

How it is loaded:
  - instructions: read from prompts/prompt.md at build time
  - model: OPENAI_MODEL, reached through the Portkey gateway (see config.py)
  - tools: search_products and get_product_details from tools.py
  - output: a structured ChatReply (message + product cards)
"""

from pathlib import Path

from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

import catalogue
from config import (
    MODEL_NAME,
    PORTKEY_BASE_URL,
    PORTKEY_PROVIDER,
    require_api_key,
)
from deps import ChatDeps
from models import ChatReply
from tools import (
    get_current_product,
    get_product_info,
    get_product_stock,
    recommend_size,
    search_products,
)

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "prompt.md"

_agent: Agent[ChatDeps, ChatReply] | None = None


def build_agent() -> Agent[ChatDeps, ChatReply]:
    """Construct a fresh agent wired to Portkey, with the shop tools and deps."""
    key = require_api_key()
    client = AsyncOpenAI(
        api_key=key,
        base_url=PORTKEY_BASE_URL,
        default_headers={
            "x-portkey-api-key": key,
            "x-portkey-provider": PORTKEY_PROVIDER,
        },
    )
    model = OpenAIResponsesModel(
        MODEL_NAME, provider=OpenAIProvider(openai_client=client)
    )
    agent = Agent(
        model,
        deps_type=ChatDeps,
        instructions=PROMPT_PATH.read_text(encoding="utf-8"),
        output_type=ChatReply,
        tools=[
            search_products,
            get_product_info,
            get_product_stock,
            get_current_product,
            recommend_size,
        ],
    )

    @agent.instructions
    def _customer_and_page_context(ctx: RunContext[ChatDeps]) -> str:
        """Inject who the shopper is and what they are viewing, per request."""
        lines: list[str] = []
        deps = ctx.deps
        if deps.first_name:
            who = deps.first_name
            if deps.email:
                who += f" ({deps.email})"
            lines.append(
                f"You are speaking with {who}, a signed-in customer. You may "
                f"greet them by first name. Do not read out their email."
            )
        else:
            lines.append("You are speaking with a guest (not signed in).")

        if deps.current_product_id:
            detail = catalogue.get_detail(deps.current_product_id)
            if detail is not None:
                lines.append(
                    f"The shopper is currently viewing the product page for "
                    f"\"{detail.name}\" (product_id: {detail.product_id}). If they "
                    f"say \"this\", \"it\", or similar, they mean this product; use "
                    f"get_current_product for its details."
                )
        return " ".join(lines)

    return agent


def get_agent() -> Agent[ChatDeps, ChatReply]:
    """Return the shared agent, constructing it on first use."""
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent
