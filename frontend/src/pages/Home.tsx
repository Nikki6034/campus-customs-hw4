import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { listProducts, formatPrice, type ProductSummary } from "../api/client";
import Reveal from "../components/Reveal";
import Marquee from "../components/Marquee";

export default function Home() {
  const [products, setProducts] = useState<ProductSummary[]>([]);

  useEffect(() => {
    listProducts()
      .then(setProducts)
      .catch(() => setProducts([]));
  }, []);

  const hero = products[0];
  const featured = products.slice(1, 4);
  const marquee = products.slice(0, 14);

  return (
    <div className="home">
      {/* Image-led hero: copy on the left, a real product on the right. */}
      <section className="editorial">
        <div className="editorial-grid">
          <div className="editorial-copy">
            <p className="eyebrow">New Haven · Est. for the Blue</p>
            <h1 className="display">
              Worn to the library.
              <br />
              Kept for a lifetime.
            </h1>
            <p className="editorial-lede">
              Yale apparel with the weight, the fit and the quiet confidence of
              clothes you reach for first — season after season, long after the
              degree.
            </p>
            <div className="hero-actions">
              <Link to="/products" className="btn btn-solid btn-lg">
                Shop the collection
              </Link>
              <Link to="/about" className="btn btn-ghost btn-lg">
                The house
              </Link>
            </div>
          </div>

          {hero && (
            <Link to={`/products/${hero.product_id}`} className="editorial-hero-product">
              <div className="hero-frame">
                <img src={hero.image_url} alt={hero.name} />
              </div>
              <div className="hero-product-meta">
                <span className="hero-product-tag">This week's pick</span>
                <span className="hero-product-name">{hero.name}</span>
                <span className="hero-product-price">{formatPrice(hero.price)}</span>
              </div>
            </Link>
          )}
        </div>
      </section>

      {/* Moving product presentation */}
      <Marquee products={marquee} />

      {/* Shop by identity */}
      <section className="editorial-band shopby">
        <Reveal>
          <p className="eyebrow">Find what's yours</p>
          <h2 className="display-sm">Shop your corner of campus</h2>
          <div className="shopby-groups">
            <div className="shopby-group">
              <span className="shopby-label">By sport</span>
              <div className="shopby-tiles">
                {["Hockey", "Football", "Baseball", "Tennis", "Soccer"].map((t) => (
                  <Link key={t} to={`/products?q=${encodeURIComponent(t)}`} className="shopby-tile">
                    {t}
                  </Link>
                ))}
              </div>
            </div>
            <div className="shopby-group">
              <span className="shopby-label">By school &amp; college</span>
              <div className="shopby-tiles">
                {["Law", "Medicine", "Divinity", "Art", "Branford"].map((t) => (
                  <Link key={t} to={`/products?q=${encodeURIComponent(t)}`} className="shopby-tile">
                    {t}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </Reveal>
      </section>

      {/* House pillars */}
      <section className="editorial-band">
        <Reveal className="pillars">
          <article>
            <span className="pillar-no">01</span>
            <h3>Built heavy</h3>
            <p>
              Fleece with real weight and seams that outlast a laundry room. If a
              sweatshirt can't survive four years, we don't print on it.
            </p>
          </article>
          <article>
            <span className="pillar-no">02</span>
            <h3>Made for the blue</h3>
            <p>
              Residential colleges, rivalry weekends, the schools within the
              school. Whatever corner of campus is yours, it lives on a label.
            </p>
          </article>
          <article>
            <span className="pillar-no">03</span>
            <h3>Worn well after</h3>
            <p>
              Our favourite photographs arrive years later — faded, softened, and
              still the first thing out of the drawer.
            </p>
          </article>
        </Reveal>
      </section>

      {/* Featured, editorial grid */}
      {featured.length > 0 && (
        <section className="editorial-feature">
          <Reveal className="section-head">
            <div>
              <p className="eyebrow">The edit</p>
              <h2 className="display-sm">Most wanted this week</h2>
            </div>
            <Link to="/products" className="text-link">
              See everything
            </Link>
          </Reveal>
          <div className="grid grid-3">
            {featured.map((p, i) => (
              <Reveal key={p.product_id} delay={i * 90}>
                <Link to={`/products/${p.product_id}`} className="card">
                  <div className="card-img">
                    <img src={p.image_url} alt={p.name} loading="lazy" />
                    <span className="card-view">View</span>
                    {p.total_stock === 0 ? (
                      <span className="badge">Sold out</span>
                    ) : (
                      p.total_stock <= 15 && (
                        <span className="badge badge-low">
                          Only {p.total_stock} left
                        </span>
                      )
                    )}
                  </div>
                  <div className="card-body">
                    <h4>{p.name}</h4>
                    <p className="price">{formatPrice(p.price)}</p>
                  </div>
                </Link>
              </Reveal>
            ))}
          </div>
        </section>
      )}

      {/* Closing statement */}
      <section className="statement">
        <Reveal>
          <p className="eyebrow">The long test</p>
          <p className="statement-text">
            We judge our work on a slow timescale — not whether it sells in
            September, but whether it's still in rotation a decade later.
          </p>
          <Link to="/products" className="btn btn-ghost btn-lg">
            Begin
          </Link>
        </Reveal>
      </section>
    </div>
  );
}
