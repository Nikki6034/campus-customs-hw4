import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  getProduct,
  getRelatedProducts,
  formatPrice,
  type Product,
  type ProductSummary,
} from "../api/client";
import SizeFinder from "../components/SizeFinder";
import { useCart } from "../cart/context";

export default function ProductDetail() {
  const { productId = "" } = useParams();
  const [product, setProduct] = useState<Product | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedSize, setSelectedSize] = useState<string | null>(null);
  const [related, setRelated] = useState<ProductSummary[]>([]);
  const cart = useCart();

  // App.tsx keys this component by productId, so navigating between products
  // remounts it with fresh state instead of resetting it here.
  useEffect(() => {
    getProduct(productId)
      .then(setProduct)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : String(err)),
      );
    getRelatedProducts(productId)
      .then(setRelated)
      .catch(() => setRelated([]));
  }, [productId]);

  if (error) {
    return (
      <div className="page page-narrow">
        <p className="notice error">Couldn't load this product: {error}</p>
        <Link to="/products" className="text-link">
          ← Back to all products
        </Link>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="page">
        <div className="detail" aria-hidden="true">
          <div className="detail-media skeleton skeleton-media" />
          <div className="detail-info">
            <div className="skeleton skeleton-line" style={{ width: "40%" }} />
            <div
              className="skeleton skeleton-line"
              style={{ width: "75%", height: "2rem", margin: "0.5rem 0 1rem" }}
            />
            <div className="skeleton skeleton-line" style={{ width: "25%" }} />
            <div className="skeleton skeleton-line" style={{ width: "100%" }} />
            <div className="skeleton skeleton-line" style={{ width: "90%" }} />
            <div className="skeleton skeleton-line" style={{ width: "60%" }} />
          </div>
        </div>
      </div>
    );
  }

  const soldOut = product.total_stock === 0;
  const chosen = product.inventory.find((s) => s.size === selectedSize);

  return (
    <div className="page">
      <Link to="/products" className="text-link back">
        ← All products
      </Link>

      <div className="detail">
        <div className="detail-media">
          <img src={product.image_url} alt={product.name} />
        </div>

        <div className="detail-info">
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="detail-price">{formatPrice(product.price)}</p>

          <p className="detail-desc">{product.description}</p>

          {product.colors.length > 0 && (
            <div className="detail-block">
              <h3>Colours</h3>
              <ul className="chips">
                {product.colors.map((c) => (
                  <li key={c} className="chip">
                    {c}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="detail-block">
            <h3>Size</h3>
            <div className="sizes">
              {product.inventory.map((s) => {
                const out = s.quantity === 0;
                const active = s.size === selectedSize;
                return (
                  <button
                    key={s.size}
                    type="button"
                    disabled={out}
                    onClick={() => setSelectedSize(s.size)}
                    className={`size${active ? " active" : ""}${out ? " out" : ""}`}
                    title={out ? "Out of stock" : `${s.quantity} in stock`}
                  >
                    {s.size}
                  </button>
                );
              })}
            </div>
            <p
              className={
                (chosen && chosen.quantity <= 5) || (!chosen && product.total_stock <= 15)
                  ? "stock-line urgent"
                  : "stock-line"
              }
            >
              {soldOut
                ? "Sold out in every size."
                : chosen
                  ? chosen.quantity <= 5
                    ? `Almost gone — only ${chosen.quantity} left in ${chosen.size}.`
                    : `${chosen.quantity} left in ${chosen.size}.`
                  : product.total_stock <= 15
                    ? `Selling fast — only ${product.total_stock} left across sizes.`
                    : `${product.total_stock} in stock across sizes — pick a size.`}
            </p>
          </div>

          <SizeFinder
            onRecommend={(size) => {
              // Pre-select the recommended size only if it's in stock here.
              const row = product.inventory.find((s) => s.size === size);
              if (row && row.quantity > 0) setSelectedSize(size);
            }}
          />

          <button
            type="button"
            className="btn btn-solid btn-lg btn-block"
            disabled={soldOut || !selectedSize}
            onClick={() => {
              if (!selectedSize) return;
              cart.add({
                productId: product.product_id,
                name: product.name,
                imageUrl: product.image_url,
                price: product.price,
                size: selectedSize,
              });
              cart.open();
            }}
          >
            {soldOut
              ? "Sold out"
              : selectedSize
                ? `Add ${selectedSize} to bag`
                : "Select a size"}
          </button>

          {product.search_tags.length > 0 && (
            <div className="detail-block">
              <h3>Tags</h3>
              <ul className="chips muted">
                {product.search_tags.map((t) => (
                  <li key={t} className="chip">
                    {t}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {related.length > 0 && (
        <section className="related">
          <div className="section-head">
            <div>
              <p className="eyebrow">Styling</p>
              <h2 className="display-sm">Pairs well with</h2>
            </div>
          </div>
          <div className="grid grid-4">
            {related.map((p) => (
              <Link key={p.product_id} to={`/products/${p.product_id}`} className="card">
                <div className="card-img">
                  <img src={p.image_url} alt={p.name} loading="lazy" />
                  <span className="card-view">View</span>
                  {p.total_stock === 0 ? (
                    <span className="badge">Sold out</span>
                  ) : (
                    p.total_stock <= 15 && (
                      <span className="badge badge-low">Only {p.total_stock} left</span>
                    )
                  )}
                </div>
                <div className="card-body">
                  <h4>{p.name}</h4>
                  <p className="price">{formatPrice(p.price)}</p>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
