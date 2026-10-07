"""Per-request dependencies passed to the shop agent.

Pydantic AI's deps pattern: one typed object handed to `agent.run(..., deps=...)`
that dynamic instructions and tools read via `RunContext`. It carries who the
shopper is (so the agent can greet them by name and scope memory) and what they
are currently looking at (so "do you have this in pink" resolves to the right
product).
"""

from dataclasses import dataclass


@dataclass
class ChatDeps:
    # Identity — present only for logged-in shoppers; None for guests.
    user_id: int | None = None
    first_name: str | None = None
    email: str | None = None

    # Page context — the product the shopper is viewing right now, if any.
    current_product_id: str | None = None

    @property
    def is_logged_in(self) -> bool:
        return self.user_id is not None
