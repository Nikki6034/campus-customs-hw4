# Campus Customs — Design

Direction: **modern heritage luxury** — an editorial, fashion-house aesthetic
(closer to Dior than streetwear), chosen because Campus Customs sells Yale
collegiate apparel and heritage luxury flatters that subject where streetwear
would fight it.

## Design system

- **Typography.** Cormorant Garamond (an elegant serif) for display headings and
  product names; Jost (a clean geometric sans) for navigation, UI, and small
  uppercase letter-spaced labels. Loaded from Google Fonts with system fallbacks.
- **Palette.** Warm ivory ground, deep Yale navy, a muted brass/gold accent, and
  near-black ink — restrained and editorial. Navy is the brand colour.
- **Details.** Near-square corners, hairline rules, generous whitespace, small
  uppercase letter-spaced labels — the vocabulary of a fashion house.

## Motion ("moving product presentation")

- **Image-led hero** — copy on the left, a real featured product (framed,
  gently floating, priced) on the right, so shoppers see something covetable on
  arrival.
- **Product marquee** — a slow, continuously scrolling band of product imagery
  that pauses on hover; each tile links to its detail page.
- **Scroll reveals** — sections and cards fade/slide in as they enter the
  viewport (IntersectionObserver).
- **Card hover** — image zoom with a "View" label.
- All motion is disabled under `prefers-reduced-motion`.

## Desire

- **Real scarcity.** Low-stock items show a gold "Only N left" badge and the
  detail page warns "Almost gone — only N left in L". All from real inventory,
  never fabricated.
- **Clean over loud.** The innovation is behavioural (chat that updates the page,
  an AI fit finder, agent memory, DB-grounded recommendations), not decorative —
  a calm surface over a smart core.

## Components

Nav (sticky, serif wordmark, bag counter), editorial hero, marquee, product grid
with hover, product detail (sticky image + sizes + size finder + "pairs well
with"), slide-out bag, chat widget, forms, loading skeletons. One shared card
component is used for catalogue, chat results and cross-sell, so every card opens
the same detail view.
