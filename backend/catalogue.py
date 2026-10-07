"""Read-only catalogue access shared by the products API and the agent tools.

Centralises the JSON-in-TEXT parsing, image-URL mapping, desirability ranking
and keyword search so the website and the chatbot see exactly the same product
data. Everything here reads through the read-only connection in db.py.
"""

import json
import re
import sqlite3
from functools import lru_cache

from db import connect
from models import (
    Product,
    ProductCard,
    ProductInfo,
    ProductSummary,
    SizeAvailability,
    SizeStock,
    StockInfo,
)

# Order sizes the way a shopper expects, not alphabetically.
SIZE_ORDER = {"XS": 0, "S": 1, "M": 2, "L": 3, "XL": 4, "XXL": 5}

# Words too common to help a product search.
_STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "with", "of", "to", "in", "on",
    "do", "you", "have", "any", "some", "me", "i", "want", "need", "looking",
    "show", "got", "is", "are", "my", "your", "that", "this", "it", "please",
}


def parse_json_list(raw: str) -> list[str]:
    """colors and search_tags are JSON arrays stored in TEXT columns."""
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return []
    return [str(v) for v in value] if isinstance(value, list) else []


def short_description(description: str) -> str:
    """First sentence of a description, for a card."""
    match = re.search(r"^(.*?[.!?])(\s|$)", description.strip())
    sentence = match.group(1) if match else description.strip()
    return sentence if len(sentence) <= 160 else sentence[:157].rstrip() + "..."


def image_url(image_file_path: str) -> str:
    """Map the stored relative path onto the served static route."""
    return f"/images/{image_file_path.removeprefix('products/')}"


def _desirability(
    total_stock: int,
    sizes_in_stock: int,
    tag_count: int,
    max_stock: int,
    max_tags: int,
) -> float:
    """Rank products for the grid; see output/harness.md §4.3."""
    availability = total_stock / max_stock if max_stock else 0.0
    coverage = sizes_in_stock / 6.0
    richness = tag_count / max_tags if max_tags else 0.0
    return round(0.45 * availability + 0.35 * coverage + 0.20 * richness, 4)


@lru_cache(maxsize=1)
def load_summaries() -> tuple[ProductSummary, ...]:
    """Read every product once and cache it; the dataset is static."""
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT c.product_id, c.name, c.garment_type, c.description,
                   c.colors, c.search_tags, c.image_file_path, c.price,
                   COALESCE(SUM(i.quantity), 0) AS total_stock,
                   COALESCE(SUM(i.quantity > 0), 0) AS sizes_in_stock
            FROM catalogue c
            LEFT JOIN inventory i ON i.product_id = c.product_id
            GROUP BY c.product_id
            """
        ).fetchall()

    tag_counts = {r["product_id"]: len(parse_json_list(r["search_tags"])) for r in rows}
    max_stock = max((r["total_stock"] for r in rows), default=0)
    max_tags = max(tag_counts.values(), default=0)

    summaries = [
        ProductSummary(
            product_id=r["product_id"],
            name=r["name"],
            garment_type=r["garment_type"],
            short_description=short_description(r["description"]),
            colors=parse_json_list(r["colors"]),
            price=r["price"],
            image_url=image_url(r["image_file_path"]),
            total_stock=r["total_stock"],
            desirability=_desirability(
                r["total_stock"],
                r["sizes_in_stock"],
                tag_counts[r["product_id"]],
                max_stock,
                max_tags,
            ),
        )
        for r in rows
    ]
    summaries.sort(key=lambda p: (-p.desirability, p.name))
    return tuple(summaries)


def get_detail(product_id: str) -> Product | None:
    """Full detail for one product, including per-size stock. None if unknown."""
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            return None
        inventory_rows = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?",
            (product_id,),
        ).fetchall()

    inventory = sorted(
        (SizeStock(size=r["size"], quantity=r["quantity"]) for r in inventory_rows),
        key=lambda s: SIZE_ORDER.get(s.size.upper(), 99),
    )
    return Product(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=parse_json_list(row["colors"]),
        search_tags=parse_json_list(row["search_tags"]),
        image_file_path=row["image_file_path"],
        image_url=image_url(row["image_file_path"]),
        price=row["price"],
        inventory=inventory,
        total_stock=sum(s.quantity for s in inventory),
    )


# Map common shopper words onto the catalogue's own vocabulary.
_SYNONYMS = {
    "tee": "t-shirt",
    "tshirt": "t-shirt",
    "sweater": "sweatshirt",
    "quarterzip": "quarter-zip",
    "zip": "quarter-zip",
    "sweatshirts": "sweatshirt",
}


def _stem(word: str) -> str:
    """Crude singulariser so 'hoodies' matches 'hoodie'."""
    if len(word) > 3 and word.endswith("s"):
        return word[:-1]
    return word


def _term_variants(term: str) -> set[str]:
    """A query term plus its stem and any synonym, for substring matching."""
    variants = {term, _stem(term)}
    if term in _SYNONYMS:
        variants.add(_SYNONYMS[term])
    if _stem(term) in _SYNONYMS:
        variants.add(_SYNONYMS[_stem(term)])
    return variants


def get_info(product_id: str) -> ProductInfo | None:
    """Descriptive facts (incl. price) for one product. None if unknown.

    Reads straight from the catalogue table, so prices and descriptions are
    always the real stored values — never invented.
    """
    detail = get_detail(product_id)
    if detail is None:
        return None
    return ProductInfo(
        product_id=detail.product_id,
        name=detail.name,
        garment_type=detail.garment_type,
        description=detail.description,
        colors=detail.colors,
        price=detail.price,
    )


def get_stock(product_id: str) -> StockInfo | None:
    """Real per-size availability for one product. None if unknown.

    Quantities come from the inventory table; a size with quantity 0 is reported
    as out of stock rather than hidden.
    """
    detail = get_detail(product_id)
    if detail is None:
        return None
    sizes = [
        SizeAvailability(size=s.size, quantity=s.quantity, in_stock=s.quantity > 0)
        for s in detail.inventory
    ]
    return StockInfo(
        product_id=detail.product_id,
        name=detail.name,
        sizes=sizes,
        total_stock=detail.total_stock,
        in_stock=detail.total_stock > 0,
    )


@lru_cache(maxsize=1)
def _tags_by_id() -> dict[str, set[str]]:
    """product_id -> lowercased search_tags, for relatedness scoring."""
    with connect() as conn:
        rows = conn.execute("SELECT product_id, search_tags FROM catalogue").fetchall()
    return {
        r["product_id"]: {t.lower() for t in parse_json_list(r["search_tags"])}
        for r in rows
    }


def related(product_id: str, limit: int = 4) -> list[ProductSummary]:
    """Products that pair well with this one, by shared search tags.

    Scores other products by how many tags they share with the target, then by
    desirability; prefers in-stock items. Excludes the product itself. Uses the
    real catalogue tags, so the suggestions are genuine, not invented.
    """
    tags = _tags_by_id()
    target = tags.get(product_id)
    if not target:
        return []
    summaries = load_summaries()
    scored: list[tuple[int, float, ProductSummary]] = []
    for s in summaries:
        if s.product_id == product_id:
            continue
        shared = len(target & tags.get(s.product_id, set()))
        if shared == 0:
            continue
        in_stock_bonus = 1 if s.total_stock > 0 else 0
        scored.append((shared + in_stock_bonus, s.desirability, s))
    scored.sort(key=lambda item: (-item[0], -item[1]))
    return [s for _, _, s in scored[:limit]]


def _summary_haystack(s: ProductSummary) -> str:
    return " ".join(
        [s.name, s.garment_type, s.short_description, " ".join(s.colors)]
    ).lower()


def search(query: str, limit: int = 6) -> list[ProductSummary]:
    """Keyword search over name, type, description and colours.

    Scores each product by how many query terms it matches (allowing for plural
    forms and common synonyms), then falls back to desirability for ordering.
    Avoids sending the whole catalogue to the model: returns only top matches.
    """
    terms = [
        t for t in re.findall(r"[a-z0-9]+", query.lower()) if t not in _STOPWORDS
    ]
    summaries = load_summaries()
    if not terms:
        return list(summaries[:limit])

    scored: list[tuple[int, float, ProductSummary]] = []
    for s in summaries:
        haystack = _summary_haystack(s)
        hits = sum(
            1 for t in terms if any(v in haystack for v in _term_variants(t))
        )
        if hits:
            scored.append((hits, s.desirability, s))

    scored.sort(key=lambda item: (-item[0], -item[1]))
    return [s for _, _, s in scored[:limit]]


def to_card(summary: ProductSummary) -> ProductCard:
    return ProductCard(
        product_id=summary.product_id,
        name=summary.name,
        price=summary.price,
        image_url=summary.image_url,
        short_description=summary.short_description,
        garment_type=summary.garment_type,
        in_stock=summary.total_stock > 0,
    )


@lru_cache(maxsize=1)
def _summary_by_id() -> dict[str, ProductSummary]:
    return {s.product_id: s for s in load_summaries()}


def ground_cards(cards: list[ProductCard]) -> list[ProductCard]:
    """Reconcile the agent's product cards against the database.

    Accuracy and safety guard: the model is told never to invent products, but
    this makes it impossible for one to slip through to the shopper. Every card
    is matched by product_id to the catalogue; unknown ids are dropped, and the
    name, price, image, description and stock are rebuilt from the database — so
    a fabricated price or image can never be displayed. Order and de-duplication
    are preserved.
    """
    by_id = _summary_by_id()
    grounded: list[ProductCard] = []
    seen: set[str] = set()
    for card in cards:
        summary = by_id.get(card.product_id)
        if summary is None or card.product_id in seen:
            continue
        seen.add(card.product_id)
        grounded.append(to_card(summary))
    return grounded
