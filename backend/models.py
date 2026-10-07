"""Pydantic types for the Campus Customs API.

Shapes follow the 11-key product payload implied by chat_messages.products_json
in the dataset (see output/harness.md §3.6), so the frontend and any later
agent consume the same contract.
"""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from security import MIN_PASSWORD_LENGTH


class SizeStock(BaseModel):
    """Stock for one size of one product."""

    size: str
    quantity: int

    @property
    def in_stock(self) -> bool:
        return self.quantity > 0


class ProductSummary(BaseModel):
    """What a product card on the Products page needs."""

    product_id: str
    name: str
    garment_type: str
    short_description: str = Field(
        description="First sentence of the description, for the card."
    )
    colors: list[str]
    price: float
    image_url: str
    total_stock: int
    desirability: float = Field(
        description="Ranking score used to order the grid; see harness.md."
    )


class Product(BaseModel):
    """Full product detail, matching the dataset's own payload shape."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    search_tags: list[str]
    image_file_path: str
    image_url: str
    price: float
    inventory: list[SizeStock]
    total_stock: int


class SignupRequest(BaseModel):
    """Account creation input. Passwords are validated here, never stored."""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(
        default=None, max_length=30, description="Optional, for shipping."
    )
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=256)
    confirm_password: str

    @field_validator("first_name", "last_name")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()

    @field_validator("phone")
    @classmethod
    def _clean_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def _passwords_match(self) -> "SignupRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class PublicUser(BaseModel):
    """A user as returned to the client. Never includes the password hash."""

    id: int
    first_name: str | None
    last_name: str | None
    email: str
    phone: str | None = None


class ProductInfo(BaseModel):
    """Result of the product-info tool: the descriptive facts a shopper asks about.

    Fields are the shopper-facing catalogue attributes — what the product is, how
    it reads, its colours, and its price. Price lives here because it is a static
    product attribute, so no separate price tool is needed. Internal retrieval
    metadata (search_tags) and stock are deliberately excluded: stock is the
    other tool's job, and tags are not a customer-facing fact.
    """

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    price: float


class SizeAvailability(BaseModel):
    """Stock for one size, with an explicit out-of-stock flag."""

    size: str
    quantity: int
    in_stock: bool


class StockInfo(BaseModel):
    """Result of the stock tool: real per-size availability from the database.

    `sizes` carries the ground-truth quantity for every size so the agent never
    invents numbers; `in_stock` per size lets it say plainly when a size is sold
    out. `total_stock` and the top-level `in_stock` summarise the product.
    """

    product_id: str
    name: str
    sizes: list[SizeAvailability]
    total_stock: int
    in_stock: bool


class ProductCard(BaseModel):
    """A compact product reference the chatbot shows in the chat widget.

    Smaller than ProductSummary: just what a card inside a chat bubble needs.
    """

    product_id: str
    name: str
    price: float
    image_url: str
    short_description: str
    garment_type: str
    in_stock: bool


class ChatReply(BaseModel):
    """Structured output produced by the shop agent.

    The agent returns a spoken reply plus any products it decided to surface,
    so the frontend can render text and product cards from one response.
    """

    message: str = Field(
        description="The assistant's reply text, in the Campus Customs voice."
    )
    products: list[ProductCard] = Field(
        default_factory=list,
        description="Products to show as cards alongside the reply, if any.",
    )


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, description="Prompt sent to the agent.")
    # Identity of a logged-in shopper (from the client). Both are verified
    # against the users table before any history is read or written; guests
    # leave these null and simply are not persisted.
    user_id: int | None = None
    email: str | None = None
    # Page context: the product the shopper is currently viewing, so "this"
    # resolves to the right item.
    current_product_id: str | None = None


class ChatResponse(BaseModel):
    """What POST /api/chat returns to the website."""

    reply: str
    products: list[ProductCard] = Field(default_factory=list)
    stub: bool = Field(
        default=False, description="True when no model was called."
    )


class SizeChartRow(BaseModel):
    """One row of the unisex size chart, in US/UK with chest in inches and cm."""

    size: str
    us: str
    uk: str
    chest_in: str
    chest_cm: str


class SizeRecommendationRequest(BaseModel):
    height: float = Field(gt=0, description="Height (cm if metric, inches if imperial).")
    weight: float = Field(gt=0, description="Weight (kg if metric, lb if imperial).")
    units: Literal["metric", "imperial"] = "metric"


class SizeRecommendation(BaseModel):
    recommended_size: str
    us: str
    uk: str
    chest_in: str
    chest_cm: str
    rationale: str
    note: str


class StoredMessage(BaseModel):
    """One past chat turn, for reloading a returning shopper's conversation."""

    role: str  # "user" or "assistant"
    content: str
    products: list[ProductCard] = Field(default_factory=list)


class AuditEntry(BaseModel):
    """One line of the append-only agent audit trail.

    A tool-call entry has `tool_name` with short `args`/`result` and no
    `stop_reason`; a run-end entry has `stop_reason` and no `tool_name`.
    """

    time: str  # ISO 8601 UTC
    tool_name: str | None = None
    args: str | None = None
    result: str | None = None
    stop_reason: str | None = None


# ProductCard is also used as the stored-history card shape.
ChatProductCard = ProductCard
