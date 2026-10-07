# Homework 4 — Campus Customs Shop Harness

Running document for Homework 4. Each problem appends its section here.

## 1. System overview

Campus Customs sells Yale merchandise. Homework 4 builds a storefront with a
shopping assistant:

- **Frontend** — React + Vite + TypeScript (`frontend/`)
- **Backend** — FastAPI + Pydantic AI (`backend/`)
- **Models** — routed through the Portkey gateway, never the OpenAI API directly
- **Data** — `data/campus_customs.db` (SQLite) plus `data/products/` images

Credentials come from `API_PORTKEY_API_KEY` or `PORTKEY_API_KEY`; no key is
hard-coded. Commands run from the `Homework 4` directory.

## 2. Input data

- `data/campus_customs.db` — four tables: `catalogue`, `inventory`, `users`,
  `chat_messages`.
- `data/products/` — 102 product images, one per catalogue row.

## 3. Database schema

Read read-only (`mode=ro`); the database was not modified during inspection.

### 3.1 `catalogue` — the product master (102 rows)

One row per product. The source of truth for what the shop sells and the
retrieval surface the chatbot searches over.

| Field | Type | Why it matters |
|---|---|---|
| `product_id` | TEXT, PK | Readable slug (`basic-hoodie-big-yale`). The join key to `inventory` and the stable id the frontend puts in URLs and the chatbot cites when recommending. |
| `name` | TEXT | What the shopper actually reads on a card or in a reply. The only field safe to show verbatim in chat. |
| `garment_type` | TEXT | The natural filter axis ("show me hoodies"). **Not a clean vocabulary** — see §3.5. |
| `description` | TEXT | Richest signal for semantic matching. Encodes color, graphics, fit and materials, so it answers "something with a bulldog on it" that structured fields cannot. |
| `colors` | TEXT (JSON array) | Backs colour filtering and the honest "we don't have that in pink" answer. Must be parsed, not string-matched. |
| `search_tags` | TEXT (JSON array) | Curated keywords for retrieval — rivalry terms, residential colleges, graphic motifs. Cheap high-precision keyword layer before any model call. |
| `image_file_path` | TEXT | Relative path (`products/<slug>.jpg`) the API turns into a served URL. Without it a product card is just text. |
| `price` | REAL | Needed for display, budget filters ("under $50"), and sorting. $32.00–$98.00, mean $58.48. |

### 3.2 `inventory` — stock per size (612 rows)

Separates *what exists* from *how many are left*, so one product carries six
independent stock levels.

| Field | Type | Why it matters |
|---|---|---|
| `id` | INTEGER, PK | Surrogate key; no business meaning. |
| `product_id` | TEXT → `catalogue` | Ties stock to the product. Join target for "is this available?". |
| `size` | TEXT | XS, S, M, L, XL, XXL. The size picker on a product page and the chatbot's follow-up question. |
| `quantity` | INTEGER | 0–25. Decides in-stock vs sold-out. The chatbot must respect it or it will promise goods the shop cannot ship. |

Shape: a complete 102 × 6 grid. `UNIQUE(product_id, size)` prevents duplicates.
Total 5,920 units across **145 zero-quantity rows**, so "out of stock in your
size" is a real path, not an edge case.

### 3.3 `users` — accounts (3 rows)

| Field | Type | Why it matters |
|---|---|---|
| `id` | INTEGER, PK | Foreign key target for `chat_messages`; identifies the session owner. |
| `name` | TEXT | Display name. Redundant with `first_name`/`last_name` — see §3.5. |
| `email` | TEXT, **UNIQUE** | The real login identifier. Uniqueness is enforced, so it is the safe lookup key. |
| `password_hash` | TEXT | PBKDF2, ~94 chars. Never a plaintext password and must never leave the backend or appear in an API response. |
| `created_at` | TEXT | Defaults to `datetime('now')`. Account age. |
| `first_name` | TEXT, nullable | Added later by `ALTER TABLE`. Nullable, so greetings must tolerate NULL. |
| `last_name` | TEXT, nullable | Same. |

### 3.4 `chat_messages` — conversation history (22 rows)

Gives the assistant memory across turns and shows the payload shape the
finished app returned.

| Field | Type | Why it matters |
|---|---|---|
| `id` | INTEGER, PK | Orders the transcript. |
| `user_id` | INTEGER → `users` | Scopes history to one person; the filter that stops conversations leaking between users. |
| `role` | TEXT | `user` or `assistant` (11 each). Maps directly to the message list sent to the model. |
| `content` | TEXT | Message text. Assistant replies are Markdown, so the frontend must render it. |
| `products_json` | TEXT, nullable | Products attached to a reply. Populated on all 11 assistant turns and none of the 11 user turns — see §3.6. |
| `created_at` | TEXT | Defaults to `datetime('now')`. Orders and ages the conversation. |

Relationships: `catalogue` 1—many `inventory`; `users` 1—many `chat_messages`.

### 3.5 Data quality findings

1. **`garment_type` is an uncontrolled vocabulary.** 22 distinct values with
   obvious duplicates: `short-sleeve t-shirt` (16) and `short-sleeve T-shirt`
   (6) differ only in case; `hoodie` (5), `pullover hoodie` (18),
   `hooded sweatshirt` (1) and `hooded pullover sweatshirt` (1) describe the
   same garment. A literal `WHERE garment_type = 'hoodie'` returns 5 rows,
   while 27 products match `LIKE '%hood%'`. Normalize, or match semantically.
2. **`colors` and `search_tags` are JSON in TEXT columns.** Not natively
   filterable without `json_each()`; parse them in Python.
3. **Foreign keys are declared but unenforced.** SQLite ignores them unless
   `PRAGMA foreign_keys = ON` is set per connection. Integrity is currently
   intact: zero orphan inventory rows, zero products without inventory.
4. **`users.name` is redundant**, equal to `first_name + ' ' + last_name` for
   all 3 rows. Residue from the `ALTER TABLE`; pick one representation.
5. **145 of 612 inventory rows are zero**, so out-of-stock handling is required
   for correctness, not polish.

### 3.6 The product payload contract

Entries inside `products_json` carry **11 keys**: the 8 catalogue fields plus
`image_url`, `inventory` and `total_stock`. Those three do not exist in
`catalogue` — they are computed. This is effectively the product shape the
finished frontend consumed, and a useful target for our own API:

```
product_id, name, garment_type, description, colors, search_tags,
image_file_path, price            # from catalogue
image_url                         # servable URL built from image_file_path
inventory                         # per-size stock from the inventory table
total_stock                       # summed quantity across sizes
```

## 4. Problem 3 — Storefront scaffold

### 4.1 Shape

```
frontend/src/
├── App.tsx                  routes + layout
├── api/client.ts            typed backend client
├── components/
│   ├── NavBar.tsx           Home · Products · About Us · Log In · Create Account
│   └── ChatWidget.tsx       docked bottom-right, calls the backend
└── pages/
    ├── Home.tsx             hero, three pillars, three most-wanted products
    ├── Products.tsx         full grid, ranked by desirability
    ├── ProductDetail.tsx    Zara-style split: image left, detail right
    ├── About.tsx            original brand copy
    ├── Login.tsx            form scaffold, not wired
    └── CreateAccount.tsx    form scaffold, not wired
```

Routes: `/`, `/products`, `/products/:productId`, `/about`, `/login`,
`/create-account`. Vite proxies `/api` and `/images` to FastAPI on port 8000,
so the relative `image_file_path` values from the database work unchanged.

### 4.2 API added this problem

| Endpoint | Purpose |
|---|---|
| `GET /api/products` | All 102 products as cards, most desirable first |
| `GET /api/products/{id}` | Full detail with per-size stock; 404 when unknown |
| `GET /images/{file}` | Product photographs, served from `data/products/` |
| `POST /api/chat` | Stub reply; becomes the agent in Problem 5 |

`backend/app/db.py` opens SQLite with `mode=ro`, so the serving layer cannot
write to the dataset even by accident. `PRAGMA foreign_keys = ON` is set per
connection, since §3.5 noted the declared keys are otherwise unenforced.

### 4.3 Desirability ranking

The grid is ordered by a blend of three signals that exist in the data:

```
desirability = 0.45 * (total_stock / max_stock)      # availability
             + 0.35 * (sizes_in_stock / 6)           # size coverage
             + 0.20 * (tag_count / max_tags)         # marketing richness
```

Reasoning: a shop surfaces what it can actually sell. Deep stock signals a
line the shop invested in, full size coverage means more shoppers can buy it,
and a richly tagged product is one the merchandiser wrote copy for. Normalizing
against the dataset's real maxima rather than hard-coded constants keeps the
scale honest — an early version capped at 90 units and flattened the top of the
range into ties. Scores now span 0.3075–0.95 with 97 distinct values across
102 products. Name breaks remaining ties so the order is stable between loads.

### 4.4 Shop behaviour driven by the data

- **Out of stock is a first-class state.** §3.5 found 145 zero-quantity rows,
  so cards show a "Sold out" badge, size buttons for empty sizes are disabled
  and struck through, and the add-to-bag button refuses until a stocked size
  is chosen.
- **Per-size counts are shown**, not just in/out, because `inventory` carries
  real quantities worth surfacing ("2 left in XL").
- **`short_description`** is the first sentence of `description`, so cards stay
  even while detail pages keep the full prose.
- **Colours and tags** are parsed from their JSON-in-TEXT columns and rendered
  as chips.

### 4.5 Chat

`ChatWidget` posts to `POST /api/chat` and renders the reply. The backend's
`CHAT_MODE` defaults to `stub`, returning a canned response with `stub: true`
and calling no model. Setting `CHAT_MODE=agent` routes the same endpoint
through the Pydantic AI agent already wired to Portkey. Problem 5 flips that
default; no frontend change is needed.

### 4.6 Copy

Home and About Us are written from scratch for Campus Customs. The brief was
to take the spirit of a Yale merchandise store, so the voice leans on
specifics — residential colleges, graduate schools, rivalry weekends, the
long life of a heavy sweatshirt. No wording was copied from any existing site.

### 4.7 Verification

- `tsc -b && vite build` — clean
- `oxlint src` — no warnings (an earlier `set-state-in-effect` warning was
  fixed by keying the detail page on `productId` so it remounts per product)
- All **102** product images fetched through the Vite proxy — 0 broken
- All six routes return 200
- `GET /api/products/nope` → 404
- Database unmodified: clean `git status` on `data/`, no `-wal`/`-shm` files

Not verified visually: the in-app browser preview could not attach on this
machine and no Chrome instance was connected, so layout and styling have not
been eyeballed — only the markup, types, data and asset wiring were checked.

## 5. Problem 4 — Accounts and login

### 5.1 Flow

- **Create account** (`/create-account`) collects first name, last name, email,
  optional phone (for shipping), password and confirm password. On success the
  shopper is logged in and returned home.
- **Log in** (`/login`) collects email and password.
- The nav bar swaps "Log In / Create Account" for a greeting and "Log Out" once
  signed in.

New accounts are inserted into the existing `users` table. An optional `phone`
column is added to that table once, idempotently, on startup
(`ensure_phone_column`), since the seeded schema has none.

### 5.2 API added this problem

| Endpoint | Purpose |
|---|---|
| `POST /api/auth/signup` | Create an account; returns the public user (201) |
| `POST /api/auth/login` | Verify credentials; returns the public user (200) |

Both return the `PublicUser` shape — `id, first_name, last_name, email, phone`.
**No endpoint ever returns the password or its hash.**

### 5.3 What is stored for a user

`id`, `name` (first + last, to satisfy the existing NOT NULL column),
`first_name`, `last_name`, `email` (unique, stored lower-cased), optional
`phone`, `created_at`, and `password_hash`. The raw password is **never**
stored, logged, or returned.

### 5.4 How passwords are protected

- **One-way hashing.** Passwords are run through PBKDF2-HMAC-SHA256 before
  touching the database. A database dump reveals no passwords.
- **600,000 iterations** (OWASP's 2023 floor for this algorithm), making each
  brute-force guess against a stolen hash deliberately expensive.
- **Per-user random 16-byte salt**, so identical passwords hash differently and
  precomputed rainbow tables do not apply.
- **Constant-time comparison** (`hmac.compare_digest`) so response timing does
  not leak how much of a hash matched.
- **Self-describing hash** `pbkdf2_sha256$<iterations>$<salt>$<digest>`. Because
  the cost is stored in the hash, it can be raised later without locking anyone
  out. (The seeded hashes omitted the iteration count, which is exactly why the
  test user had to be re-hashed into this format — see §5.6.)
- **No user enumeration.** Login returns the same "Invalid email or password."
  for an unknown email and a wrong password, and runs a dummy verification for
  unknown emails so timing is uniform.
- **No password echo.** A custom validation handler strips submitted values out
  of error responses, so a mistyped password is never reflected back or logged.
- **Minimum length 8**, enforced server-side by Pydantic (and hinted in the UI).
- **Password verification is confined to the login endpoint**; there is no API
  that tests a password against a hash in bulk.

The client stores only the non-sensitive `PublicUser` in `localStorage` for
display — never a password, hash, or token.

### 5.5 Not in scope

Sessions/JWTs, password reset, email verification, and rate limiting are not
part of this problem. Rate limiting would be the next hardening step for a real
deployment and is noted here as future work.

### 5.6 The seeded test user

The seeded hashes used a 3-part format with no iteration count, so they cannot
be verified by the login code. The known test account
(`test@campuscustoms.yale.edu` / `password`) was re-hashed into the secure
self-describing format via `backend/scripts/reseed_test_user.py`, so it logs in
normally. The other two seeded users (ada, tauhid) keep their original hashes;
they are not used for login.

### 5.7 Verification

Tested end to end through the Vite proxy (the browser's real path):

- Log in as `test@campuscustoms.yale.edu` / `password` → 200
- Wrong password for the test user → 401, generic message
- Unknown email → 401, same generic message
- Create a new account (with and without phone) → 201, then log in → 200
- Mismatched passwords → 422, **no password echoed**, no server error
- Password under 8 chars → 422, message reduced to "Invalid password."
- Invalid email → 422
- Duplicate email → 409
- Database check: no plaintext password appears in any stored hash; every new
  hash uses `pbkdf2_sha256$600000$...`
- All throwaway test accounts were deleted; the table is back to the three
  seeded users.

## 6. Problem 5 — Pydantic AI shop agent

### 6.1 Layout (runs from `backend/`)

The backend was flattened so it runs exactly as asked, from inside `backend/`:

```
uvicorn main:app --reload --port 8000
```

```
backend/
├── main.py          FastAPI app + the /api/chat route (run this)
├── agent.py         builds the Pydantic AI agent (prompt + model + tools)
├── tools.py         tools the agent can call
├── models.py        Pydantic / Pydantic AI structured types
├── catalogue.py     shared read-only product access (router + tools use it)
├── config.py        env + Portkey settings
├── db.py            SQLite connections
├── security.py      password hashing (Problem 4)
├── prompts/
│   └── prompt.md    system prompt: voice + safety basics
└── routers/
    ├── products.py  /api/products, /api/products/{id}
    └── auth.py      /api/auth/signup, /api/auth/login
```

### 6.2 How the frontend talks to FastAPI

1. The chat widget (`frontend/src/components/ChatWidget.tsx`) POSTs
   `{ "message": "..." }` to `/api/chat`.
2. In development the Vite dev server proxies `/api` (and `/images`) to
   `http://localhost:8000`, so the browser uses same-origin relative paths. In
   production `VITE_API_BASE_URL` can point at the backend instead. CORS also
   allows the Vite origin.
3. `main.py` validates the body as `ChatRequest`, runs the agent, and returns
   `ChatResponse` — `{ reply, products, stub }`.
4. The widget renders `reply` as a chat bubble and each item in `products` as a
   small card linking to that product's detail page.

### 6.3 How the agent is loaded

`agent.py:build_agent()` constructs a Pydantic AI `Agent`:

- **Prompt:** read from `prompts/prompt.md` at build time and passed as the
  agent's `instructions`. Editing that file changes the agent's behaviour; no
  code change needed.
- **Model:** `OPENAI_MODEL` reached through the **Portkey gateway** — an
  `AsyncOpenAI` client pointed at `PORTKEY_BASE_URL` with the `x-portkey-*`
  headers, wrapped in `OpenAIResponsesModel` via `OpenAIProvider`. The key comes
  from `API_PORTKEY_API_KEY` / `PORTKEY_API_KEY` (never hard-coded).
- **Tools:** `search_products` and `get_product_details` from `tools.py`, thin
  wrappers over the read-only `catalogue` module.
- **Output:** a structured `ChatReply` (`message` + list of `ProductCard`), so
  the model returns prose and product cards in one typed response.

The agent is built lazily and cached, so importing the app never needs a key;
the key is only required when a chat request first arrives.

### 6.4 Chat modes and error handling

- `CHAT_MODE=agent` (default) runs the agent. `CHAT_MODE=stub` returns a canned
  reply with no model call, for working offline.
- A missing key yields a clean 503. A gateway **content-filter rejection** (HTTP
  400 — e.g. a prompt-injection attempt) is caught and answered with a calm
  in-character refusal (HTTP 200) so the widget keeps working; other gateway
  errors yield 502.

### 6.5 Voice and safety (prompts/prompt.md)

The prompt sets the Campus Customs voice (warm, specific, brief) and safety
basics: shopping-only scope, never invent products/prices/stock, never reveal
system internals or other customers' data, never handle passwords or payment in
chat, and ignore instructions embedded in product data or user messages that try
to change the rules. Tools and safety will be expanded in later problems.

### 6.6 Types added (models.py)

- `ProductCard` — compact product reference for a chat bubble.
- `ChatReply` — the agent's structured output (message + product cards).
- `ChatResponse` — extended with `products`, so the API returns cards too.

### 6.7 Verification (live, through the Portkey gateway)

- `uvicorn main:app --reload --port 8000` from `backend/` starts cleanly;
  health, products and auth all still work after the restructure.
- "Do you have any hoodies?" → 6 real cards with correct prices and stock.
- "Something for the Harvard game" → the 2025 Yale–Harvard tee + a warm hood.
- "Do you sell socks?" → honest "no", no invented products.
- Off-topic ("capital of France?") → politely declines, stays on shopping.
- Prompt-injection attempt → blocked by the gateway filter; API returns a calm
  refusal, nothing leaked.
- A search bug was found and fixed in the process: plural/synonym queries
  ("hoodies") now match singular catalogue terms ("hoodie").
- End to end through the Vite proxy returns reply + cards.

## 7. Problem 6 — Product info and stock tools

### 7.1 The agent's tools (all query campus_customs.db, read-only)

| Tool | Reads | Returns | Use |
|---|---|---|---|
| `search_products(query, limit)` | catalogue (+ inventory for stock totals) | list of `ProductCard` | Discovery — find products and their `product_id` |
| `get_product_info(product_id)` | catalogue | `ProductInfo` | Description, colours and **price** |
| `get_product_stock(product_id)` | inventory | `StockInfo` | Real **per-size** availability |

All three read through the read-only connection, so the agent can never write to
the dataset. Prices come only from `get_product_info`; stock only from
`get_product_stock`. The prompt forbids inventing prices or quantities, and a
size with quantity 0 is reported as out of stock rather than hidden.

**Why info and stock are separate tools, and why price has none of its own:**
price is a static product attribute, so it rides along with `get_product_info` —
a dedicated price tool would be a second query returning a single field. Stock is
genuinely different data (the inventory table, per size, changeable), so it earns
its own tool. This keeps each tool's result focused and cheap.

### 7.2 Lookup result models and the fields chosen

`ProductInfo` (in `models.py`):

| Field | Why |
|---|---|
| `product_id` | Stable id to link to the detail page and to pass to the stock tool |
| `name` | What the shopper reads |
| `garment_type` | Answers "what is it" |
| `description` | The actual descriptive answer (fabric, fit, graphic) |
| `colors` | A common question, parsed from the JSON-in-TEXT column |
| `price` | A common question; a static attribute, so it lives here |

Deliberately excluded: `search_tags` (internal retrieval metadata, not a
customer-facing fact) and stock (that is the other tool's job — separation of
concerns keeps each result clean).

`StockInfo` (in `models.py`), with a `SizeAvailability` per size:

| Field | Why |
|---|---|
| `product_id`, `name` | Identify the product the stock belongs to |
| `sizes[]` → `size`, `quantity`, `in_stock` | Ground-truth quantity per size so the agent never invents numbers; the explicit `in_stock` flag lets it say "out of stock" plainly |
| `total_stock` | Quick "do you have any at all" summary |
| `in_stock` | True if any size is available |

### 7.3 Verification (live, through Portkey)

For `baseball-left-chest-crewneck` (XS and XL are 0 in the data):

- "How much is it?" → "$58" (matches the catalogue exactly)
- "Available in XL?" → "out of stock in XL… available in S, M, L, and XXL"
- "What sizes are in stock?" → "S, M, L, XXL; XS and XL out of stock"

Unknown ids return None from both tools; the direct data checks confirm the
tools read real quantities and never fabricate.

## 8. Problem 7 — Chat search that updates the page

A question in the chat ("what hoodies do you have?") now updates the website: the
agent's matches render as product cards on the Products page, and each one opens
the Problem 3 detail view.

### 8.1 How search results reach the page

```
shopper types in ChatWidget
      │  POST /api/chat { message }
      ▼
main.py → agent.run → ChatReply { message, products: ProductCard[] }
      │  (search_products already queried the catalogue, read-only)
      ▼
ChatResponse { reply, products, stub }   ← the API contract
      │
ChatWidget receives it:
   • shows the reply (and compact cards) in the chat bubble
   • if products.length > 0: setResults(query, products) into ChatResultsContext
     and navigate("/products")
      ▼
Products page reads ChatResultsContext:
   • when results are present, it renders them as the grid under
     'Results for "<query>"', with a "Show all products" button to clear
   • each card is the same <ProductCardLink> used for the full catalogue,
     linking to /products/<product_id>
      ▼
clicking any card (chat-placed or catalogue) → the Problem 3 detail view
```

### 8.2 The contract

`POST /api/chat` returns `ChatResponse.products: ProductCard[]` — the structured
matches. Each `ProductCard` carries `product_id`, `name`, `price`, `image_url`,
`short_description`, `garment_type`, `in_stock` — exactly the "image, name,
price, short info" a card needs, plus the `product_id` that makes it clickable
through to the detail page. No new endpoint was needed; Problem 5 already
returns this shape, and Problem 7 renders it on the page.

### 8.3 Frontend pieces

- `chat/context.ts` + `chat/ChatResultsProvider.tsx` — a small shared store for
  the latest chat query and its matches.
- `ChatWidget.tsx` — writes results to the store and navigates to the grid.
- `Products.tsx` — renders chat results when present (else the full catalogue),
  via one shared `ProductCardLink` so chat-placed and catalogue cards behave
  identically and both open the detail view.

### 8.4 Verification

- "what hoodies do you have?" → 3 structured matches, each with all card fields.
- Every returned `product_id` resolves to `GET /api/products/{id}` → 200, so the
  chat-placed cards open the detail view just like catalogue cards.
- Verified through the Vite proxy (the browser's real path). Typecheck and lint
  clean.

## 9. Problem 8 — Customer memory

A signed-in shopper's conversation is saved and reloaded when they return, the
agent knows who it is talking to, and page context lets "do you have this in
pink?" resolve to the product being viewed. Guests can chat, but nothing is
stored.

### 9.1 How chat history is saved

- Stored in the dataset's existing `chat_messages` table — `user_id`, `role`
  (`user`/`assistant`), `content`, `products_json`, `created_at`. No new table
  was needed; this is what that table is for.
- After each exchange, **for logged-in shoppers only**, `history.append_exchange`
  writes two rows: the user's message and the assistant's reply (with any
  product cards serialised into `products_json`). Guests are never written.
- On return, `GET /api/chat/history?user_id=&email=` returns the saved turns and
  the chat widget renders them, so the shopper picks up where they left off.
- For the agent's own memory, `history.load_history_as_messages` rebuilds the
  last 20 turns as Pydantic AI `ModelRequest`/`ModelResponse` messages and
  passes them to `agent.run(..., message_history=...)`, so the model actually
  remembers earlier turns across sessions (verified: it recalls a stated
  preference in a later, separate request).

### 9.2 Customer fields the agent sees

Identity is passed with the Pydantic AI **deps** pattern — a `ChatDeps` dataclass
handed to `agent.run(..., deps=...)` and read by dynamic instructions and tools
via `RunContext`:

| Field | Source | Why the agent sees it |
|---|---|---|
| `user_id` | verified from the request | scopes which history to load/save; marks logged-in vs guest |
| `first_name` | `users.first_name` | greet a returning customer by name |
| `email` | `users.email` | identifies the account; the prompt forbids reading it back aloud |
| `current_product_id` | the page the shopper is on | resolve "this"/"it" |

The agent is **not** given the password hash or any other customer's data. A
dynamic instruction turns these deps into a short context line each request
("You are speaking with <name>… currently viewing <product>…").

### 9.3 How identity is verified (and its limit)

The client sends `user_id` + `email`; `history.resolve_customer` only treats the
shopper as logged-in when both match a real `users` row. Honest limitation:
Problem 4 added no session tokens, so this trusts a value the client supplies —
adequate for the assignment, but a production app would authenticate the chat
request with a real session/JWT before reading or writing anyone's history. This
is the same caveat noted in §5.5.

### 9.4 How page context is passed

- The chat widget derives the current product from the URL (`/products/<id>`
  via `useLocation`) and sends it as `current_product_id` on every message.
- It reaches the agent through `ChatDeps.current_product_id`. A dynamic
  instruction names the viewed product, and the `get_current_product` tool
  returns its full detail (colours, price, per-size stock) so the agent can
  answer "this in pink / this in large" against real data — never invented.

### 9.5 Verification (live)

- "do you have this in pink?" while viewing the Harvard tee → "No… heather gray,
  white, red, navy blue" (the real colours; no product comes in pink).
- A logged-in shopper states a preference, then a **separate** request asks it
  back → recalled correctly from saved history.
- Guest chat writes **zero** rows; logged-in chat writes two per exchange.
- `GET /api/chat/history` returns saved turns; a mismatched email is treated as a
  guest (no history). All test rows were cleaned up; the table is back to the
  seeded 22.

## 10. Problem 9 — Usability improvements

Four improvements to the working shop: two frontend, two agent/backend.

### 10.1 Frontend

**Products filter bar.** The Products page now has a search box, a category
filter, and an "in stock only" toggle, all client-side over the loaded list. The
category filter groups the catalogue's 22 messy `garment_type` values (harness
§3.5) into a few shopper-friendly buckets — Hoodies, Crewnecks, T-shirts,
Quarter-zips, Jackets, Sweatshirts, Other — so browsing 102 products is quick
without needing the chat. An empty result shows a "Clear filters" shortcut.

**Loading skeletons.** The product grid and the detail page now show shimmer
skeletons while data loads, instead of bare "Loading…" text — steadier layout
and a more finished feel. The shimmer respects `prefers-reduced-motion`.

### 10.2 Agent / backend

**Database grounding of product cards (accuracy + safety).** After the agent
replies, `catalogue.ground_cards` reconciles every product card against the
catalogue by `product_id`: unknown ids are dropped, duplicates removed, and the
name, price, image, description and stock are rebuilt from the database. The
model is already told never to invent products, but this makes it *impossible*
for a fabricated product — or a wrong price or image — to reach the shopper.
Verified: an invented id is dropped and a tampered price is corrected to the DB
value.

**Per-chat usage limits (cost efficiency + safety).** Each `agent.run` is now
bounded by `UsageLimits(request_limit=6, tool_calls_limit=8)`, so a malformed or
adversarial prompt cannot drive a runaway, expensive loop of model/tool calls. A
normal answer uses only a few; hitting the bound degrades to a calm 503 asking
the shopper to rephrase, rather than burning budget. Combined with the capped
message-history window (20 turns) and compact tool payloads, this keeps the cost
per chat predictable.

## 11. Problem 10 — Brand aesthetic

A full visual restyle into a "modern heritage luxury" direction — editorial,
fashion-house-adjacent (closer to Dior than streetwear), chosen because Campus
Customs sells Yale collegiate apparel and heritage luxury suits that subject far
better than streetwear would.

### 11.1 Design system

- **Type:** Cormorant Garamond (elegant serif) for display headings and product
  names; Jost (clean geometric sans) for UI, nav and uppercase letter-spaced
  labels. Loaded from Google Fonts with a system-serif/sans fallback.
- **Palette:** warm ivory ground, deep Yale navy, a muted brass/gold accent, and
  near-black ink — restrained and editorial. Navy was already the brand colour.
- **Details:** near-square corners, hairline rules, generous whitespace, small
  uppercase letter-spaced labels — the vocabulary of a fashion house.

### 11.2 Motion ("moving product presentation")

- **Editorial hero** on a navy field that rises in on load.
- **Product marquee** (`Marquee.tsx`): a slow, continuously scrolling band of
  product imagery that pauses on hover; each tile links to its detail page.
- **Scroll reveals** (`Reveal.tsx`): sections and cards fade/slide in as they
  enter the viewport, via `IntersectionObserver`.
- **Card hover:** image zoom with a "View" label fading up.
- All motion is disabled under `prefers-reduced-motion`.

### 11.3 Scope and safety

Purely presentational: the restyle is CSS plus two small presentational
components and an editorial Home layout. No route, API, data, agent, auth or
business logic changed, so Problems 3–9 behave exactly as before — every card
still opens the detail view, filters and chat still work. Typecheck and lint are
clean.

## 12. Size guidance (height/weight → size, with cm/in and US/UK)

Shoppers can get a size recommendation from their height and weight, with
measurements in both inches and cm and both US and UK labels — in chat and on
the product page.

### 12.1 The standard used

`sizing.py` holds a standard unisex top chart (XS–XXL) with body chest ranges in
inches and cm. Conversions use the standard 1 in = 2.54 cm and 1 lb = 0.4536 kg.
For these unisex letter-sized tops US and UK letter sizes coincide, so both
columns show the same letter and the response is explicit that the chest
measurement is the real determinant — rather than inventing a false difference.

The catalogue has no body data, so this is a general fit guide, not a per-garment
measurement, and every response says so.

### 12.2 Recommendation logic

`sizing.recommend(height, weight, units)` — `units` is "metric" (cm, kg) or
"imperial" (in, lb). Weight sets a base size against standard unisex weight
bands; height then nudges it (≥188 cm up, ≤163 cm down). It returns the size with
US/UK labels, chest in inches and cm, a short rationale, and a note to confirm by
chest and to size up for an oversized look.

### 12.3 Where it is exposed

- **Agent tool** `recommend_size(height, weight, units)` — the shopper can just
  say "I'm 5'10" and 170 lbs, what size?"; the agent converts to inches/lb (or
  cm/kg) and calls it, then presents the size with US/UK and both unit systems.
- **`GET /api/size-guide`** — the full chart for the product page.
- **`POST /api/size-recommendation`** — `{height, weight, units}` → recommendation.
- **Product page** — a "Size guide & fit finder" panel (`SizeFinder.tsx`): a
  metric/imperial toggle, height/weight inputs, the recommendation, and the full
  US/UK/in/cm chart. A recommended size that is in stock is pre-selected on the
  size picker.

### 12.4 Verification (live)

- Agent: "5 foot 10 and 170 pounds" → M, US M / UK M, 38–40 in / 97–102 cm.
- Endpoint parity: metric 178 cm / 77 kg and imperial 70 in / 170 lb both → M.
- Range sanity: petite → XS, tall-and-heavy → XXL.
- Size guide and recommendation both reachable through the Vite proxy.

## 13. Purchase-intent features

Four features to turn browsing into buying, chosen with the user.

### 13.1 Working bag (client-side cart)

A cart context (`cart/context.ts`, `CartProvider.tsx`) persisted to
localStorage. "Add to bag" on the product page now adds the selected size and
opens a slide-out drawer (`CartDrawer.tsx`) with quantity controls, remove, a
live subtotal, and a bag counter in the nav. Checkout is out of scope and the
button says so plainly rather than being another dead control.

### 13.2 "Complete the look" cross-sell

`catalogue.related(product_id)` scores other products by shared `search_tags`
(tie-broken by desirability, preferring in-stock), exposed as
`GET /api/products/{id}/related`. The detail page shows a "Pairs well with"
grid — real suggestions from the catalogue, never invented.

### 13.3 Shop-by-identity entry points

A Home "Shop your corner of campus" section with tiles by sport (Hockey,
Football, …) and school/college (Law, Divinity, Branford, …). Each links to
`/products?q=<term>`; the Products page seeds its search from the param (the page
is remounted on param change, so no sync effect). Belonging drives desire for
collegiate merch.

### 13.4 Energy band (removed)

A bold serif word ticker was added under the hero, then removed at the user's
request — they found the scrolling text distracting with no real use. The
product marquee remains the home page's motion.

### 13.5 Verification

- Related endpoint: a football tee → the other sports tees + a crewneck; unknown
  id → 404.
- Cart math, counter and persistence build clean; "Shop by" routes serve with the
  query param. Typecheck and lint clean.

## 14. Audit trail (append-only)

`output/audit_trail.json` is an append-only JSON array recording what the agent
did, run after run. It is never wiped: each chat extends the file, and a server
restart does not reset it (verified: 5 → 7 entries across a restart).

Written by `backend/audit.py` from `main.py` after every chat:

- **One entry per tool call** the agent made — `time` (ISO-8601 UTC),
  `tool_name`, short `args`, short `result` (each capped at ~220 chars). The
  internal `final_result` output tool is excluded.
- **One run-end entry** with the `stop_reason`: `stop` for a normal finish, or
  `usage_limit_exceeded`, `content_filtered`, `model_http_error`, `error` for the
  guarded failure paths.

If the file is ever unreadable it is moved aside (`.corrupt.json`) rather than
overwritten, so prior data is never lost. Writes are serialised with a lock.

## 15. Reference

### 15.1 Model fields in `models.py` and why

| Model | Fields | Why these |
|---|---|---|
| `ProductSummary` | product_id, name, garment_type, short_description, colors, price, image_url, total_stock, desirability | Exactly what a catalogue **card** needs; `desirability` orders the grid, `short_description` keeps cards tidy. |
| `Product` | + description, search_tags, image_file_path, inventory[] | Full **detail** view; mirrors the dataset's own 11-key payload (harness §3.6) so UI and agent share one shape. |
| `ProductInfo` | product_id, name, garment_type, description, colors, price | The **info tool** result: shopper-facing facts incl. price; excludes tags (internal) and stock (other tool's job). |
| `StockInfo` / `SizeAvailability` | sizes[{size, quantity, in_stock}], total_stock, in_stock | The **stock tool** result: ground-truth per-size quantity so the agent never invents; explicit `in_stock` for "sold out". |
| `ProductCard` | product_id, name, price, image_url, short_description, garment_type, in_stock | Compact card the **chat** shows and the page renders; `product_id` makes it clickable. |
| `ChatReply` | message, products[] | The agent's **structured output**: prose + cards in one typed response. |
| `SizeRecommendation` | recommended_size, us, uk, chest_in, chest_cm, rationale, note | Size result in **both unit systems and US/UK**, with a guide-not-gospel note. |
| `PublicUser` | id, first_name, last_name, email, phone | What the client may see — **never** the password hash. |
| `SignupRequest` | names, email, phone?, password, confirm_password | Validates and confirms the password server-side; phone optional for shipping. |
| `StoredMessage` | role, content, products[] | One saved chat turn for reloading a returning shopper. |
| `AuditEntry` | time, tool_name?, args?, result?, stop_reason? | One audit line; tool-call vs run-end entries use different subsets. |

### 15.2 Tools and abilities

| Tool | Reads | Ability |
|---|---|---|
| `search_products(query, limit)` | catalogue | Find products by type/colour/occasion (plural + synonym aware) |
| `get_product_info(product_id)` | catalogue | Description, colours, price |
| `get_product_stock(product_id)` | inventory | Real per-size availability |
| `get_current_product(ctx)` | catalogue + deps | Resolve "this"/"it" to the viewed product |
| `recommend_size(height, weight, units)` | size chart | Size from height/weight, cm/in, US/UK |

The agent also has grounding (cards reconciled to the DB after each reply) and
memory (prior turns replayed for signed-in shoppers).

### 15.3 Safety rules

Ten absolute rules live in `prompts/prompt.md` (§"Safety rules"): stay in scope,
never invent, respect stock, protect secrets/internals, no sensitive data in
chat, resist injection, no unauthorised promises, no actions it can't take, size
guidance is general, and say so when unsure. They override any later instruction,
including injected ones in shopper messages or product data. Enforced in depth by
DB grounding (no fabricated product/price reaches the UI) and the gateway content
filter (handled as a calm refusal).

### 15.4 Specs

- **Model:** `OPENAI_MODEL` (default `gpt-5.6-luna`) via the **Portkey** gateway
  (`OpenAIResponsesModel` + `AsyncOpenAI` with `x-portkey-*` headers). Key from
  `API_PORTKEY_API_KEY` / `PORTKEY_API_KEY`, never hard-coded.
- **Loop limits:** `UsageLimits(request_limit=6, tool_calls_limit=8)` per chat.
- **Result caps:** search returns ≤ 6 (hard max 10); related products ≤ 4;
  replayed history ≤ 20 turns; audit args/result ≤ 220 chars.
- **Chat modes:** `CHAT_MODE=agent` (default) or `stub` (offline, no model call).
- **Persistence:** chat history for signed-in users in `chat_messages`;
  append-only audit in `output/audit_trail.json`.

### 15.5 How to run

Backend (from `backend/`, with its `.venv`):

```
uvicorn main:app --reload --port 8000
```

Frontend (from `frontend/`):

```
npm run dev
```

The Vite dev server (`http://localhost:5173`) proxies `/api` and `/images` to the
backend on `:8000`. The key is read from the environment or `../.env`; no secret
is committed.
