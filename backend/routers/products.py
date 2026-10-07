"""Product endpoints, served read-only from campus_customs.db."""

from fastapi import APIRouter, HTTPException

import catalogue
from models import Product, ProductSummary

router = APIRouter(prefix="/api", tags=["products"])


@router.get("/products", response_model=list[ProductSummary])
async def list_products() -> list[ProductSummary]:
    """All products, most desirable first."""
    return list(catalogue.load_summaries())


@router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str) -> Product:
    """Full detail for one product, including per-size stock."""
    product = catalogue.get_detail(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/products/{product_id}/related", response_model=list[ProductSummary])
async def related_products(product_id: str) -> list[ProductSummary]:
    """Products that pair well with this one, by shared tags."""
    if catalogue.get_detail(product_id) is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return catalogue.related(product_id)
