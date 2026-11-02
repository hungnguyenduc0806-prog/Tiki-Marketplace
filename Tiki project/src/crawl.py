"""
Crawl snapshot san pham Tiki theo ngay.

Cach dung (chay tu thu muc goc cua project):
    python -m src.crawl                  # dung CATEGORY_ID mac dinh
    python -m src.crawl 1591             # chi dinh category khac
    python -m src.crawl 1591 --probe     # chi tham do, khong crawl het

Moi lan chay sinh ra 2 file:
    data/raw/tiki_<cat>_<ngay>.json        - JSON tho, giu nguyen
    data/processed/tiki_<cat>_<ngay>.csv   - da parse, dung de phan tich

Chay 1 lan/ngay. Sau 6 tuan ban co chuoi thoi gian that.
"""

import json
import random
import sys
import time
from datetime import datetime

import pandas as pd
import requests

import config
from src.parse import dig, parse_item

# ----------------------------------------------------------------
# Session
# ----------------------------------------------------------------

SESSION = requests.Session()        # mot session cho ca chuong trinh
SESSION.headers.update(config.HEADERS)


# ----------------------------------------------------------------
# Lay du lieu
# ----------------------------------------------------------------

def fetch_page(category_id: int, page: int, retries: int = config.RETRIES) -> dict:
    """
    Lay mot trang ket qua.

    Chong hai loai su co khac nhau:
      - 429 (bi gioi han toc do): doc header Retry-After neu co, khong thi cho 30s
      - loi mang / timeout: thu lai voi exponential backoff + jitter (5s, 10s, 20s)

    Het luot ma van that bai thi RAISE, khong tra ve None. Tra ve None se khien
    ham goi chet o cho khac, xa noi loi that su xay ra.
    """
    params = {"limit": config.LIMIT, "category": category_id, "page": page}

    for lan in range(retries):
        try:
            r = SESSION.get(config.API_URL, params=params, timeout=config.TIMEOUT)

            if r.status_code == 429:
                cho = int(r.headers.get("Retry-After", config.RATE_LIMIT_WAIT))
                time.sleep(cho)         # bị giới hạn tốc độ, nghỉ lâu
                continue

            r.raise_for_status()
            return r.json()

        except requests.RequestException:
            if lan == retries - 1:
                raise
            cho = config.BACKOFF_BASE * 2 ** lan + random.uniform(0, 1)
            time.sleep(cho)             # chờ lâu dần: 5s, 10s, 20s

    raise requests.RequestException(
        f"Trang {page}: bi chan rate limit sau {retries} lan thu"
    )


def probe(category_id: int) -> None:
    """Tham do quy mo nganh hang truoc khi cam ket crawl 6 tuan."""
    data = fetch_page(category_id, 1)
    paging = data.get("paging", {})

    print(f"Category        : {category_id}")
    print(f"Tong san pham   : {paging.get('total')}")
    print(f"So trang        : {paging.get('last_page')}")
    print(f"Dong o trang 1  : {len(data.get('data', []))}")

    items = data.get("data", [])
    if items:
        print("\n--- Cac truong co trong 1 san pham ---")
        for k in sorted(items[0].keys()):
            print(f"  {k}")
        print("\n--- San pham dau tien (rut gon) ---")
        print(json.dumps(items[0], ensure_ascii=False, indent=2)[:1500])


# ----------------------------------------------------------------
# Chay
# ----------------------------------------------------------------

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
            print(f"  trang {page}: loi {e} - dung lai")
            break

        items = data.get("data", [])
        if not items:
            print(f"  trang {page}: rong - het du lieu")
            break

        raw_pages.append(data)

        moi = 0
        for sp in items:
            pid = sp.get("id")
            if pid in seen_ids:          # Tiki co the tra trung giua cac trang
                continue
            seen_ids.add(pid)
            rows.append(parse_item(sp, crawled_at, category_id))
            moi += 1

        print(f"  trang {page}: {len(items)} dong, {moi} moi (tong {len(rows)})")

        last_page = dig(data, "paging", "last_page")
        if last_page and page >= last_page:
            break

        time.sleep(config.DELAY)

    if not rows:
        print("Khong lay duoc du lieu nao. Kiem tra lai category_id.")
        return

    # Luu tho TRUOC - neu sau nay phat hien thieu truong, van cuu duoc
    raw_path = config.RAW_DIR / f"tiki_{category_id}_{day}.json"
    raw_path.write_text(
        json.dumps(raw_pages, ensure_ascii=False), encoding="utf-8"
    )

    df = pd.DataFrame(rows)
    csv_path = config.PROCESSED_DIR / f"tiki_{category_id}_{day}.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    # Tom tat - doc moi ngay de phat hien bat thuong som
    print(f"\n  {len(df)} san pham -> {csv_path}")
    print(f"  JSON tho          -> {raw_path}")
    print(f"  So nguoi ban      : {df['seller_id'].nunique()}")
    print(f"  So thuong hieu    : {df['brand_name'].nunique()}")
    print(f"  Gia trung vi      : {df['price'].median():,.0f} d")

    thieu_gia = df["price"].isna().sum()
    if thieu_gia:
        print(f"  CANH BAO: {thieu_gia} dong thieu gia")


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
