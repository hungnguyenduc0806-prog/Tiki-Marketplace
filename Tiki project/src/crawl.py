import json
import random
import sys
import time
from datetime import datetime

import pandas as pd
import requests

import config
from src.parse import dig, parse_item

SESSION = requests.Session()
SESSION.headers.update(config.HEADERS)

#define session get
def fetch_page(category_id: int, page: int, retries: int = config.RETRIES) -> dict:
    params = {"limit": config.LIMIT, "category": category_id, "page": page}

    for lan in range(retries):
        try: # handling rate limit, internet connection and timeout errors
            r = SESSION.get(config.API_URL, params=params, timeout=config.TIMEOUT)

            if r.status_code == 429:
                try:
                    cho = int(r.headers.get("Retry-After", config.RATE_LIMIT_WAIT))
                except ValueError:
                    cho = config.RATE_LIMIT_WAIT
                time.sleep(cho)
                cho = min(cho, 900)
                continue

            r.raise_for_status()
            return r.json()

        except requests.RequestException:
            if lan == retries - 1:
                raise
            cho = config.BACKOFF_BASE * 2 ** lan #exponential backoff
            time.sleep(cho)

    raise requests.RequestException(
        f"Page {page}: got blocked after {retries} retries"
    )


def probe(category_id: int) -> None:
    data = fetch_page(category_id, 1)
    paging = data.get("paging", {})

    print(f"Category        : {category_id}")
    print(f"Total Products  : {paging.get('total')}")
    print(f"Last Page       : {paging.get('last_page')}")
    print(f"Items on Page 1 : {len(data.get('data', []))}")

    items = data.get("data", [])
    if items:
        print("\nKeys of one product:")
        for k in sorted(items[0].keys()):
            print(f"  {k}")
        print("\nFirst Product (Summary):")
        print(json.dumps(items[0], ensure_ascii=False, indent=2)[:1500])

def crawl(category_id: int) -> None:
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    crawled_at = now.strftime("%Y-%m-%d %H:%M:%S")
    day = now.strftime("%Y%m%d")

    raw_pages, rows = [], []
    seen_ids = set()

    for page in range(1, config.MAX_PAGES + 1):
        try:
            data = fetch_page(category_id, page)
        except requests.RequestException as e:
            print(f"  Page {page}: error {e} - stopping")
            break

        items = data.get("data", [])
        if not items:
            print(f"  Page {page}: empty - no more data")
            break

        raw_pages.append(data)

        moi = 0
        for sp in items:
            pid = sp.get("id")
            if pid in seen_ids:
                continue
            seen_ids.add(pid)
            rows.append(parse_item(sp, crawled_at, category_id))
            moi += 1

        print(f"  Page {page}: {len(items)} items, {moi} new (total {len(rows)})")

        last_page = dig(data, "paging", "last_page")
        if last_page and page >= last_page:
            break

        time.sleep(config.DELAY)

    if not rows:
        print("No data fetched. Please check the category_id.")
        return

    raw_path = config.RAW_DIR / f"tiki_{category_id}_{day}.json"
    raw_path.write_text(
        json.dumps(raw_pages, ensure_ascii=False), encoding="utf-8"
    )

    df = pd.DataFrame(rows)
    csv_path = config.PROCESSED_DIR / f"tiki_{category_id}_{day}.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"\n  {len(df)} products -> {csv_path}")
    print(f"  Raw JSON          -> {raw_path}")
    print(f"  Number of sellers : {df['seller_id'].nunique()}")
    print(f"  Number of brands  : {df['brand_name'].nunique()}")
    print(f"  Median Price      : {df['price'].median():,.0f} VND")

    thieu_gia = df["price"].isna().sum()
    if thieu_gia:
        print(f"  WARNING: {thieu_gia} products missing price")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    cat = int(args[0]) if args else config.CATEGORY_ID

    if "--probe" in sys.argv:
        probe(cat)
        return

    print(f"Crawl category {cat} - {datetime.now():%Y-%m-%d %H:%M}")
    crawl(cat)


if __name__ == "__main__":
    main()
