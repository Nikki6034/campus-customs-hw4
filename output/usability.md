# Campus Customs — Usability

The usability improvements layered onto the working shop, front and back.

## Frontend

- **Filter & search bar** (Products page) — a text search, a category filter that
  groups the catalogue's 22 messy `garment_type` values into clean buckets
  (Hoodies, Crewnecks, T-shirts, Quarter-zips, Jackets, Sweatshirts), and an "in
  stock only" toggle. All instant and client-side; an empty result offers "Clear
  filters".
- **Loading skeletons** — shimmer placeholders for the grid and detail page in
  place of bare "Loading…" text, so the layout stays steady. Respects
  `prefers-reduced-motion`.
- **Working bag** — "Add to bag" adds the chosen size, a slide-out drawer shows
  the bag with quantity controls and a live subtotal, and a counter appears in
  the nav (persisted in localStorage). Checkout is honestly labelled out of
  scope rather than left as a dead control.
- **"Pairs well with"** — related products (by shared tags) on each detail page,
  for bigger baskets and easier browsing.
- **Shop-by-identity** — Home tiles by sport and school/college link to a
  pre-filtered Products page, so shoppers find the piece that is *theirs*.
- **Size guide & fit finder** — enter height/weight (metric or imperial) for a
  recommended size, with the full US/UK chart in inches and cm; an in-stock
  recommended size is pre-selected.

## Agent / backend

- **Database grounding (accuracy + safety).** After every reply, each product
  card is reconciled against the catalogue by `product_id`: invented products are
  dropped and name/price/image/stock are rebuilt from the database, so a
  fabricated product or price can never reach the shopper.
- **Per-chat usage limits (cost + safety).** `UsageLimits(request_limit=6,
  tool_calls_limit=8)` bounds each run so a bad prompt cannot drive a runaway,
  expensive loop; hitting the cap degrades to a calm message.
- **Honest failure handling.** A missing key → 503; a gateway content-filter
  rejection → a calm in-character refusal; other errors → 502. The widget always
  stays responsive.

## Chat-driven usability

Asking "what hoodies do you have?" updates the page itself — the agent's matches
render as product cards on the Products page, each opening the detail view. The
chat also answers price and stock questions from live data, remembers signed-in
shoppers, and resolves "this" to the product being viewed.
