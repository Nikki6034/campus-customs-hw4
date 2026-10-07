"""Tools the shop agent can call.

Each tool is a thin, typed wrapper over the read-only catalogue module. Keeping
them small and honest matters: the agent is told never to invent product data,
so these are its only window onto the catalogue. They return plain dicts, which
Pydantic AI serialises back to the model.

Problem 5 shipped search; Problem 6 adds focused product-info and stock lookups.
"""

from pydantic_ai import RunContext

import catalogue
import sizing
from deps import ChatDeps


def search_products(query: str, limit: int = 6) -> list[dict]:
    """Search the catalogue for products matching a shopper's query.

    Use this whenever the shopper describes what they want (a garment type,
    colour, team, occasion, or vibe). Returns up to `limit` of the best matches
    as compact product cards. Returns an empty list if nothing matches.
    """
    limit = max(1, min(limit, 10))
    return [catalogue.to_card(s).model_dump() for s in catalogue.search(query, limit)]


def get_product_info(product_id: str) -> dict | None:
    """Look up a product's description, colours and price by its id.

    Use this for any question about what a product is, how it looks, its colours,
    or how much it costs. The price and description come straight from the
    database — use them exactly; never invent or estimate. Returns None if the id
    is unknown. Get the id from search_products first.
    """
    info = catalogue.get_info(product_id)
    return info.model_dump() if info is not None else None


def get_product_stock(product_id: str) -> dict | None:
    """Look up real per-size stock for a product by its id.

    Use this for any availability or size question ("is this in stock?",
    "do you have it in XL?"). Returns the quantity for every size with an
    in_stock flag; a size with quantity 0 is out of stock. Report availability
    only from this data — never guess. Returns None if the id is unknown.
    Get the id from search_products first.
    """
    stock = catalogue.get_stock(product_id)
    return stock.model_dump() if stock is not None else None


def get_current_product(ctx: RunContext[ChatDeps]) -> dict | None:
    """Return the product the shopper is currently viewing, with full detail.

    Use this to resolve "this"/"it" when the shopper is on a product page —
    e.g. "do you have this in pink" or "is it in stock in large". Returns the
    product's description, colours, price and per-size stock, or None if the
    shopper is not on a product page.
    """
    product_id = ctx.deps.current_product_id
    if not product_id:
        return None
    detail = catalogue.get_detail(product_id)
    return detail.model_dump() if detail is not None else None


def recommend_size(height: float, weight: float, units: str = "metric") -> dict:
    """Recommend a size from a shopper's height and weight.

    Call this when the shopper gives their height and weight and wants a size.
    `units` is "metric" (height in cm, weight in kg) or "imperial" (height in
    inches, weight in pounds) — convert the shopper's figures to one of these
    first (e.g. 5'10" is 70 inches). Returns the recommended size with its US and
    UK labels and chest measurement in both inches and cm. Present the chest in
    both units and remind the shopper it is a general guide.
    """
    if units not in ("metric", "imperial"):
        units = "metric"
    return sizing.recommend(height, weight, units)
