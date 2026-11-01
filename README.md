# Tiki Marketplace Price Dynamics

Daily price-tracking pipeline for the shampoo category on Tiki
Marketplace. Collects list price, sale price, seller, and rating
for 886 SKUs across 105 sellers, storing each day as a snapshot
in PostgreSQL to build a continuous time series.

**Running since:** 2026-09 · **Snapshots:** 6+ weeks · **Rows:** ~37k

## Questions this dataset answers
- Are advertised discounts preceded by inflation of the list price?
- How does seller attrition move in a category losing market share?
- Which sellers follow price leaders, and with what lag?

## Stack
Python (requests, pandas) · PostgreSQL · Power BI

## Pipeline
`scrape.py` → raw JSON → `transform.py` → `prices` table (one row
per SKU per day, deduplicated on `(sku_id, captured_date)`)
