import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  listProducts,
  formatPrice,
  type ChatProductCard,
  type ProductSummary,
} from "../api/client";
import { useChatResults } from "../chat/context";

// Group the catalogue's many raw garment_type values (see harness §3.5) into a
// few shopper-friendly categories for the filter.
function categoryOf(garmentType: string): string {
  const t = garmentType.toLowerCase();
  if (t.includes("hood")) return "Hoodies";
  if (t.includes("quarter") || t.includes("zip")) return "Quarter-zips";
  if (t.includes("crew")) return "Crewnecks";
  if (t.includes("t-shirt") || t.includes("tee") || t.includes("t shirt"))
    return "T-shirts";
  if (t.includes("jacket") || t.includes("fleece")) return "Jackets";
  if (t.includes("sweatshirt")) return "Sweatshirts";
  return "Other";
}

// One card, used for the catalogue and for chat-driven results. Both link to
// the Problem 3 detail view.
function ProductCardLink(props: {
  productId: string;
  name: string;
  imageUrl: string;
  price: number;
  shortDescription: string;
  soldOut: boolean;
  totalStock?: number;
}) {
  const low =
    !props.soldOut && props.totalStock !== undefined && props.totalStock <= 15;
  return (
    <Link to={`/products/${props.productId}`} className="card">
      <div className="card-img">
        <img src={props.imageUrl} alt={props.name} loading="lazy" />
        {props.soldOut ? (
          <span className="badge">Sold out</span>
        ) : (
          low && <span className="badge badge-low">Only {props.totalStock} left</span>
        )}
      </div>
      <div className="card-body">
        <h4>{props.name}</h4>
        <p className="card-desc">{props.shortDescription}</p>
        <p className="price">{formatPrice(props.price)}</p>
      </div>
    </Link>
  );
}

function SkeletonGrid() {
  return (
    <div className="grid grid-4" aria-hidden="true">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="card">
          <div className="card-img skeleton" />
          <div className="card-body">
            <div className="skeleton skeleton-line" style={{ width: "70%" }} />
            <div className="skeleton skeleton-line" style={{ width: "90%" }} />
            <div className="skeleton skeleton-line" style={{ width: "30%" }} />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function Products() {
  const [products, setProducts] = useState<ProductSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { query, products: chatResults, clear } = useChatResults();

  // Filter controls (apply to the full catalogue, not chat results). The search
  // is seeded from the ?q= param; App remounts this page when ?q= changes, so no
  // effect is needed to keep them in sync.
  const [searchParams] = useSearchParams();
  const [search, setSearch] = useState(searchParams.get("q") ?? "");
  const [category, setCategory] = useState("All");
  const [inStockOnly, setInStockOnly] = useState(false);

  useEffect(() => {
    listProducts()
      .then(setProducts)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : String(err)),
      );
  }, []);

  const categories = useMemo(() => {
    if (!products) return [];
    const set = new Set(products.map((p) => categoryOf(p.garment_type)));
    return ["All", ...Array.from(set).sort()];
  }, [products]);

  const filtered = useMemo(() => {
    if (!products) return [];
    const q = search.trim().toLowerCase();
    return products.filter((p) => {
      if (category !== "All" && categoryOf(p.garment_type) !== category) return false;
      if (inStockOnly && p.total_stock === 0) return false;
      if (q) {
        const hay = `${p.name} ${p.short_description} ${p.colors.join(" ")}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [products, search, category, inStockOnly]);

  const showingChatResults = chatResults.length > 0;

  return (
    <div className="page">
      {showingChatResults ? (
        <section className="hero hero-compact">
          <p className="eyebrow">Shop assistant</p>
          <h1>Results for "{query}"</h1>
          <p className="hero-sub">
            {chatResults.length} {chatResults.length === 1 ? "match" : "matches"} the
            assistant found for you.{" "}
            <button type="button" className="text-link linkish" onClick={clear}>
              Show all products
            </button>
          </p>
        </section>
      ) : (
        <section className="hero hero-compact">
          <p className="eyebrow">The collection</p>
          <h1>Everything we make.</h1>
          <p className="hero-sub">
            Ordered by what's moving — the pieces stocked deepest, available in
            the most sizes, and asked for most often sit at the top.
          </p>
        </section>
      )}

      {showingChatResults ? (
        <div className="grid grid-4">
          {chatResults.map((p: ChatProductCard) => (
            <ProductCardLink
              key={p.product_id}
              productId={p.product_id}
              name={p.name}
              imageUrl={p.image_url}
              price={p.price}
              shortDescription={p.short_description}
              soldOut={!p.in_stock}
            />
          ))}
        </div>
      ) : (
        <>
          {error && <p className="notice error">Couldn't load products: {error}</p>}
          {!error && products === null && <SkeletonGrid />}
          {products && (
            <>
              <div className="filters">
                <input
                  type="search"
                  className="filter-search"
                  placeholder="Search products…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  aria-label="Search products"
                />
                <select
                  className="filter-select"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  aria-label="Filter by category"
                >
                  {categories.map((c) => (
                    <option key={c} value={c}>
                      {c === "All" ? "All categories" : c}
                    </option>
                  ))}
                </select>
                <label className="filter-toggle">
                  <input
                    type="checkbox"
                    checked={inStockOnly}
                    onChange={(e) => setInStockOnly(e.target.checked)}
                  />
                  In stock only
                </label>
              </div>

              <p className="result-count">
                {filtered.length} {filtered.length === 1 ? "item" : "items"}
              </p>

              {filtered.length === 0 ? (
                <p className="notice">
                  Nothing matches that.{" "}
                  <button
                    type="button"
                    className="text-link linkish"
                    onClick={() => {
                      setSearch("");
                      setCategory("All");
                      setInStockOnly(false);
                    }}
                  >
                    Clear filters
                  </button>
                </p>
              ) : (
                <div className="grid grid-4">
                  {filtered.map((p) => (
                    <ProductCardLink
                      key={p.product_id}
                      productId={p.product_id}
                      name={p.name}
                      imageUrl={p.image_url}
                      price={p.price}
                      shortDescription={p.short_description}
                      soldOut={p.total_stock === 0}
                      totalStock={p.total_stock}
                    />
                  ))}
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
