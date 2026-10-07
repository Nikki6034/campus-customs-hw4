import { Link } from "react-router-dom";
import type { ProductSummary } from "../api/client";

// A slow, continuously scrolling band of product imagery — the "moving product
// presentation". The list is duplicated so the loop is seamless; it pauses on
// hover, and each tile links to the product's detail page.
export default function Marquee({ products }: { products: ProductSummary[] }) {
  if (products.length === 0) return null;
  const row = [...products, ...products];

  return (
    <div className="marquee" aria-label="Featured products in motion">
      <div className="marquee-track">
        {row.map((p, i) => (
          <Link
            key={`${p.product_id}-${i}`}
            to={`/products/${p.product_id}`}
            className="marquee-item"
            aria-hidden={i >= products.length}
            tabIndex={i >= products.length ? -1 : 0}
          >
            <img src={p.image_url} alt={p.name} loading="lazy" />
            <span className="marquee-caption">{p.name}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
