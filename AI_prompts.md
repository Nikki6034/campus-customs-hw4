# Homework 4 — AI Prompt Log

Scenario: Campus Customs, the Yale merchandise store. Homework 4 builds a
React + Vite + TypeScript frontend against a FastAPI + Pydantic AI backend,
with all model calls routed through the Portkey gateway.

Every problem section below records:

1. the problem number and title
2. at least one initial prompt, quoted verbatim as I typed it
3. the follow-up prompts, where there were any

## Setup

### Environment and tracking

**User:** We are going to do HW 4 in AI foundations so ensure everything is tracked per problem and create a virtual environment

**Assistant action:** Created the Homework 4 virtual environment and initialized a Git repository scoped to `Homework 4`, with a `.gitignore` covering `.env`, `.venv/`, `__pycache__/`, `node_modules/`, `dist/`, and `output/` so secrets and dependencies stay out of history.

### Project stack

**User:** So for this assignement, I need a bunch of things. I am explaining the scenario. I need a react + vite + typescript frontend and a python Fast API backend using Pydantic AI. please install everything I would need for this and create appropriate frontend/backend structure. Also setup the projet to read my API key from an environment variable. Can you do these things for me please? Only need what I ASK, BUT ofc any dependency required, I will alow access

**Assistant action:** Installed Node.js v24.21.0 LTS (verified by SHA-256 checksum, no admin password needed) since it was absent and Vite requires it. Scaffolded `frontend/` with React + Vite + TypeScript and `backend/` with FastAPI, Uvicorn, and Pydantic AI in `backend/.venv`. Wired the API key to be read from an environment variable rather than hard-coded, and verified the frontend builds and the backend serves `/api/health`.

### Portkey gateway

**User:** can you see my portkey?

**Assistant action:** Found `PORTKEY_API_KEY` in the shared `AI Foundations/.env` (value never displayed). Discovered from the earlier homework that the course routes models through the Portkey gateway rather than the OpenAI API directly, and rewired the agent accordingly: an `AsyncOpenAI` client pointed at `PORTKEY_BASE_URL` with `x-portkey-api-key` and `x-portkey-provider` headers, passed to `OpenAIResponsesModel` via `OpenAIProvider`. Verified end to end — `/api/chat` returned a live response from `gpt-5.6-luna-global`.

**User:** now on i always want you to use portkey api key ok??

**Assistant action:** Saved this as a standing preference so it persists across sessions, and confirmed no direct `OPENAI_API_KEY` references remain anywhere in Homework 4.

### Dataset

**User:** Did I upload the data for HW4?

**Assistant action:** Confirmed the data was not yet in `Homework 4`, and located `data (2).zip` in Downloads.

**User:** I just downloaded data (2) in my downloads - use that

**Assistant action:** Extracted `data (2).zip` into `Homework 4/data` — `campus_customs.db` (catalogue 102, inventory 612, users 3, chat_messages 22) plus 102 product images. Verified every `image_file_path` in the catalogue resolves to a real file, and committed the dataset pristine as a baseline.

## Problem 1: AI Prompt Log

### Initial prompt

**User:** we are going to use the files extracted from the zip now so let's start. so for problem 1, we first need the AI_prompts.md so you recording these prompts

**Assistant action:** Created `AI_prompts.md` following the Homework 3 convention — one titled section per problem, each recording the prompt verbatim alongside the action it produced — and backfilled every prompt from the setup work above. This log is updated as each subsequent prompt arrives.

### Follow-up prompt

**User:** I have to still ensure you capture it so ensure that each section includes - the problem number and title - at least one problem I typed in my own words and the follow up prompts. we good?

**Assistant action:** Confirmed the required structure and made it explicit in the log: stated the three requirements at the top of the file, and gave every problem section a numbered title with `### Initial prompt` and `### Follow-up prompt` subheadings so each element is visibly present rather than implied.

## Problem 2: Understand the Database

### Initial prompt

**User:** next is problem 2 - go through the database data/campus_customs.db and understand the fields of each table. We should at least understand the catalgue, inventory and users. list all the fields/commons and  explain what the table is for? don't modify anything before showing the explanation

**Assistant action:** Inspected `data/campus_customs.db` through a read-only connection (`mode=ro`) and presented the explanation before writing anything, as instructed. Documented all four tables — `catalogue` (102 rows), `inventory` (612), `users` (3), `chat_messages` (22) — with every column, type, key and constraint. Verified the database was untouched: clean `git status`, unchanged mtime, no `-wal`/`-shm` files.

### Follow-up prompt

**User:** Now we got to build a harness file and add details of the table, it's field and why it matters for the shop or the chatbot. kepp this harness file for anything related to them until the end of the problem

**Assistant action (Problem 2 follow-up):** Created `output/harness.md` following the Homework 3 convention, with a per-field "why it matters" column framed around the shop and the chatbot. Recorded five data-quality findings — notably that `garment_type` is an uncontrolled vocabulary where an exact `'hoodie'` match returns 5 rows against 27 hoodie-like products — and documented the 11-key product payload contract implied by `products_json`. Removed `output/` from `.gitignore` so the harness and future artifacts are tracked as deliverables. This file is the running document for the rest of the problem.

## Problem 3: Scaffold the Campus Customs Storefront

### Initial prompt

**User:** Next is problem 3 and it starts with the term scaffold so i am gonna use that, you have to do scaffold a react + Vite + typescript front end for campus customs and it should include a nav bar that links to the main pages namely Home, Products, About us, Login in, create account. You can used the campus customs style wording from - https://yalebulldogblue.com/ for home and about us pages, but write it in your own true amazing voice,. DO NOT COPY THE SAME THING.

In the products page, shpw product images from catalogue - there's are the image paths in the database with basic product infor (name, price, short description). Make each product open a single item page yk like how you see on Zara with a large image on one side, product text on the other - description, price, stock/size when you have em) like a regulkar shopping site. make it look like a user would buy. Clicking a card on products should take the shopper there. also arrange it based on the items which look the most desriable. In the botto, have a chat interface and it does not need to take to an agent yet - apparently a stub that will call the backend is enough for this problem. I am gonna need the API soon to read the DB ( database) just to serve the products and images, grow it into the agent backend in problem 5

**Assistant action:** Built the storefront and the read-only API behind it. Backend: `db.py` (SQLite opened `mode=ro`), `models.py` (Pydantic types matching the dataset's own 11-key product payload), `routers/products.py` serving `GET /api/products` and `GET /api/products/{id}`, and a `/images` static mount for the product photographs. Frontend: React Router with Home, Products, Product detail, About Us, Log In and Create Account, a nav bar linking all of them, and a docked chat widget calling `POST /api/chat`, which returns a stub with no model call (`CHAT_MODE=stub`; Problem 5 flips it to `agent`). The grid is ranked by a documented desirability score blending stock depth, size coverage and tag richness. Home and About Us copy was written from scratch rather than taken from any site. Verified: clean typecheck, clean lint, all 102 images resolve, all six routes serve, unknown product 404s, and the database is untouched. Recorded in `output/harness.md` §4.

## Problem 4: Create Account and Login

### Initial prompt

**User:** Next is problem 4 - create acc and login. We need a normal create account and login flow and for create account, you are gonna need first name, last name, email, password and confirm password. I think we should do also phone number if people wanna provide that for like shippping. And for the login , email and password. New accs go into the users table and make sure to save the password so securely so no hackers whether AI or Human can access em. The DB already has a test user which we can use during buildin - email: test@campuscustoms. yale.edu and pwd: password. I am going to confirm if I can login and might also create a brand new account so once done, have it in this chat, Also update the output/harness.md with how the auth works and what you store for a user and how pwds are protected. I need it super secure so careful

**Assistant action:** Built the full auth flow. Backend: `security.py` (PBKDF2-HMAC-SHA256, 600k iterations, per-user salt, constant-time compare, self-describing hash), `routers/auth.py` (`/api/auth/signup`, `/api/auth/login`), an optional `phone` column added idempotently, uniqueness and password-match validation, no-user-enumeration login, and a validation handler that strips passwords out of error responses. Frontend: wired Create Account (first/last/email/optional phone/password/confirm) and Log In (email/password) forms, an auth context, and a nav bar that reflects the signed-in user. The seeded test user was re-hashed into the secure format so `test@campuscustoms.yale.edu` / `password` logs in. Verified end to end through the Vite proxy; all throwaway test accounts removed so the table holds only the three seeded users. Documented in `output/harness.md` §5.

### Follow-up prompt

**User:** okayy, it works! Brilliant job.

**Assistant action:** Confirmed the storefront and auth flow working in the browser.

## Problem 5: Pydantic AI Shop Agent Backend

### Initial prompt

**User:** okayy, it works! Brilliant job. No no, I don't want any account i CREATED to exist except for the test account so let's do problem 5 which is pydantic AI agent backend - WWe got to build the shop chatbot as a pydantic AI agent behind Fast API which should be plugeed into fron end chat widget and put the app in backend/main.py - the file one runs with Uvicorn. Keep the agent as these 4 files next to it - similar to HW 3 you checked - backend/prompts/prompt.md, backend/agent.py, backend/tools.py,backend/models.py which are systems prompts, agent entry/writing, tools the agent can call, Pydantic/pydantic AI structured types. In main.py, expose a chat route so a message from the website returns a replay from the agent and whatever needed for prod/auth. Use the api KEY. Post that put campus customs voice and safety basics into prompts/ptompt.md and you will expand the tools and safety later. Start or update the types in models.py for chat replies and product cards as needed. In the output/harness.md, make notes of how the frontend talks to FASTAPI and howthe agent is loaded ( prompt file + model). ensure that the backend runs from the backedn/ folder like this: uvicorn main:app --reload --port 8000

**Assistant action:** Confirmed only seeded accounts remained (no user-created ones to delete; test account intact). Restructured the backend to run as `uvicorn main:app --reload --port 8000` from `backend/`: flattened the package so `main.py`, `agent.py`, `tools.py`, `models.py` and `prompts/prompt.md` sit directly in `backend/`, with a shared `catalogue.py` for read-only product access. Built the Pydantic AI shop agent loaded from `prompts/prompt.md` + the Portkey model, with `search_products` and `get_product_details` tools and a structured `ChatReply` (message + product cards). Exposed `POST /api/chat` in `main.py`, wired the chat widget to render reply text plus product cards, and set the Campus Customs voice and safety basics in the prompt. Found and fixed a search bug (plurals/synonyms), handled content-filter rejections gracefully, and verified live through the Portkey gateway and the Vite proxy. Documented in `output/harness.md` §6.

## Problem 6: Product Info and Stock Tools

### Initial prompt

**User:** The next is problem 6 - product info and stock. I need 2 agent tools that query campus_customs.db - one for prod desciptions such as price or do you think we need another for price? it need the agent to use the database - do not invent any prices or quantities. If a size if out of stock, then it can reflect out of stock. need you to expand prompts/prompt.md so the agent can call these tools for price and stock questions. add or return types in models. py. Ensure that the tools are listed in output/harness.md and explain which model fields you chose for lookup results and why

**Assistant action:** Advised that price does not need its own tool — it is a static attribute, so it rides with the product-info lookup. Added two DB-backed tools: `get_product_info` (description, colours, price from the catalogue) and `get_product_stock` (real per-size availability from inventory, with out-of-stock sizes flagged). Added `ProductInfo`, `SizeAvailability` and `StockInfo` to `models.py`, backed by read-only `catalogue.get_info`/`get_stock`. Expanded `prompts/prompt.md` so the agent calls these tools for price and stock questions and never invents prices or quantities. Verified live: correct price ($58), correct out-of-stock XL, correct available sizes. Documented the tools and the field choices in `output/harness.md` §7.

## Problem 7: Chat Search That Updates the Page

### Initial prompt

**User:** let's do problem 7, claude. We need a chat search that updates the page essentially. When a customer asks about a type of item like what hoodies do you have, the agent should search the catalogue and the website should dynamically show those matching items as product cards like image, name, price, short info. This is an API contract - the agent returns structure product matches and then front end renders on website. I think this was meant for me, but it's pretty cool. After the dynamic prod cards are loaded by this new feature, make sure the same single item page behavior built in problem 3: each product card - including the ones the chat put on the page and should still open that detail view (large image + full info) when clicked. update prompts/prompt.md and output/harness.md so it is clear how search results reach the page

**Assistant action:** Used the existing API contract (ChatResponse.products: ProductCard[], from Problem 5) and built the frontend rendering. Added a small shared store (`chat/context.ts`, `chat/ChatResultsProvider.tsx`); the chat widget writes the agent's matches to it and navigates to the Products page, which renders them as product cards under 'Results for "<query>"' with a "Show all products" button. A single shared `ProductCardLink` is used for both chat-placed and catalogue cards, so every card opens the Problem 3 detail view. Expanded `prompts/prompt.md` so the agent returns all matches in `products` for "what X do you have" questions, and documented the full path from chat to page in `output/harness.md` §8. Verified that each chat-returned product_id resolves to a 200 detail page.

## Problem 8: Customer Memory

### Initial prompt

**User:** The next problem is customer memory - let's say a shopper is logged in - their chat history needs to be saved in the db in an appropriate table and reload it when they return. The agent should know who is talking name and email - put that in agent deps or similar clear pattern and tools the agent can call. Pass enough page context like if someone says do you have this in pink, it should know what item they are referring to. Code accordingly. Only logged in users' history needs to be recorded - guests can still chat tho. Document it in output/harness.md - how the chat history is saved, what are the customer fields the agent would be seeing, how page context is passed

**Assistant action:** Implemented customer memory using the dataset's existing `chat_messages` table. Added a `ChatDeps` dataclass (Pydantic AI deps: user_id, first_name, email, current_product_id) injected via `agent.run(deps=...)`, with dynamic instructions that greet the shopper by name and name the product they're viewing, plus a `get_current_product` tool so "this in pink" resolves to the viewed item. Logged-in exchanges are persisted (`history.append_exchange`); on return, history is reloaded both into the widget (`GET /api/chat/history`) and into the agent as Pydantic AI message history, so it remembers across sessions. Guests chat without any persistence. Identity is verified by matching user_id + email against the users table (limitation noted: no session token yet). Verified live: page context, name recall, cross-request memory, guest non-persistence. Documented in `output/harness.md` §9; cleaned up all test rows.

## Problem 9: Improve the Core Shop

### Initial prompt

**User:** Let's do problem 9 - Core shop works - improve it. Choose and implement 2 front end usability improvements, 2 agent/backend usability improvements. Front-end improvements are things that make the site look better and make it easier to use. Need agent/backend improvements that make the output better/accurate and safer. Need it to be also cost efficient

**Assistant action:** Implemented four improvements. Frontend: (1) a Products filter bar — search, category filter (grouping the 22 messy garment_type values into clean buckets), and in-stock toggle; (2) shimmer loading skeletons for the grid and detail page (respecting prefers-reduced-motion). Backend/agent: (1) database grounding — `catalogue.ground_cards` drops invented product ids and rebuilds every card's name/price/image/stock from the DB, so no fabricated product or price can reach the shopper (accuracy + safety); (2) per-chat `UsageLimits(request_limit=6, tool_calls_limit=8)` so a bad prompt can't trigger a runaway, expensive loop, degrading to a calm 503 (cost efficiency + safety). Verified grounding (invented dropped, tampered price corrected) and that normal chat still works under the limits. Documented in `output/harness.md` §10.

## Problem 10: Brand Aesthetic

### Initial prompt

**User:** For problem 10, I got to style the website - I want a high end brand aesthetic or even maybe streetwear brand aesthetic (referenced Dior and Sundae School). I like the fonts, colors, and moving product presentation. Make it creative, you decide.

**Assistant action:** Chose a "modern heritage luxury" direction (closer to Dior than streetwear), reasoning that Yale collegiate apparel suits an editorial fashion-house look. Built a full design system: Cormorant Garamond serif display + Jost sans UI (Google Fonts), a warm ivory / deep navy / brass-gold palette, near-square corners, hairline rules and uppercase letter-spaced labels. Added the "moving product presentation" the user liked: an editorial navy hero that rises in, a continuously scrolling product marquee (`Marquee.tsx`), scroll-reveal animations (`Reveal.tsx` via IntersectionObserver), and card hover zoom — all disabled under prefers-reduced-motion. The change is purely presentational (CSS + two small components + an editorial Home layout); no routes, API, data or logic changed, so Problems 3–9 still work. Documented in `output/harness.md` §11. Noted that I could not visually verify in this environment and asked the user to review.

## Size Guidance (follow-on feature)

### Prompt

**User:** yk what would help? if I tell you my height and weight, you give me size recommendations and also I'd appreciate the cm, inches and those kind of details - use standard ones for them - offer UK and US sizes

**Assistant action:** Added size guidance from height and weight. Built `sizing.py` with a standard unisex size chart (XS–XXL, chest in inches and cm) and a `recommend(height, weight, units)` function (metric or imperial, standard 2.54 cm/in and 0.4536 kg/lb conversions; weight sets a base size, height nudges it). Exposed it three ways: an agent tool `recommend_size` (so the shopper can just say "5'10", 170 lbs"), `GET /api/size-guide` and `POST /api/size-recommendation`, and a "Size guide & fit finder" panel on the product page (`SizeFinder.tsx`) with a metric/imperial toggle, a recommendation, and the full US/UK/in/cm chart; an in-stock recommended size is pre-selected. Was honest that for unisex letter-sized tops US and UK letters coincide (chest is the determinant) rather than inventing a difference. Verified live via chat and both endpoints. Documented in `output/harness.md` §12.

## Purchase-Intent Features (follow-on)

### Prompt

**User:** [after "I don't feel the urge to purchase"] chose all four levers: make the bag work, "complete the look" cross-sell, bolder/streetwear energy, shop-by-identity entry points.

**Assistant action:** Implemented all four. (1) A client-side cart (context + provider, localStorage) with a working "Add to bag", a slide-out drawer with quantity/remove/subtotal, and a nav bag counter; checkout is honestly labelled out of scope. (2) "Complete the look": `catalogue.related` by shared search_tags → `GET /api/products/{id}/related`, rendered as a "Pairs well with" grid on the detail page. (3) Shop-by-identity: a Home section of sport and school/college tiles linking to `/products?q=term`, with Products seeding its search from the param (remounted on change, no sync effect). (4) An energy band: a bold scrolling word ticker under the hero. Verified the related endpoint (football tee → sibling sports tees), 404 on unknown, and clean build/lint. Documented in `output/harness.md` §13.

## Problem 11: App Check HTML with Screenshots

### Initial prompt

**User:** Problem 11 - I had to test the live site and I already done that. I need to include clear screenshots and short captions - does the chat check the inventory level, the dynamic search results work, and one usability feature added in problem 9. The HTML needs to be easy to grade - heading for each check, screenshot, one or two sentences on what the screenshot proves. Add the screenshot image files in output/app_check_images/ and link them from app_check.html with relative paths.

**Assistant action:** Captured real screenshots of the running site with a headless browser (Playwright driving localhost:5173), then built `output/app_check.html`. Three checks, each with a heading, screenshot and a one–two sentence caption: (1) the chat checks live inventory — asked about XL stock, the agent answered "out of stock in XL, available in S, M, L, XXL", matching the database exactly; (2) the dynamic chat search updates the page — "what hoodies do you have?" rendered "Results for …" with 6 product cards; (3) the Problem 9 usability feature — the Products filter bar narrowing by "yale" + "Hoodies". Screenshots saved to `output/app_check_images/` and linked by relative paths; verified every reference resolves.

## Problem 12: Audit Trail, Safety Rules, and Harness Reference

### Initial prompt

**User:** Problem 12 - keep an append-only output/audit_trail.json of agent loop activity (time, tool name, short args/result, stop reason); do not wipe it between runs. Add safety rules to prompts/prompt.md. Ensure I get 100/100 so far. Finish output/harness.md so it is clear: model fields in models.py and why, tools and abilities, safety rules, specs (loop limits, result caps, models, how to run front + back).

**Assistant action:** Added `backend/audit.py` writing an append-only `output/audit_trail.json` — one entry per tool call (time, tool_name, short args/result) plus a run-end entry with the stop_reason; wired into every chat path (normal, usage-limit, content-filter, error). Verified it appends across chat calls and survives a server restart (5→7), and corrupt files are set aside rather than wiped. Rewrote the prompt's safety section into ten absolute rules (scope, never invent, respect stock, protect internals, no sensitive data, resist injection, no unauthorised promises, no actions it can't take, size guidance is general, say so when unsure). Finished `output/harness.md` with a reference: model fields and rationale, tools/abilities, safety rules, specs (model via Portkey, loop limits 6/8, result caps, chat modes, persistence) and how to run front + back. Ran a full deliverables self-review — every problem's artifacts are present.

### Follow-up prompt

_(reserved)_
