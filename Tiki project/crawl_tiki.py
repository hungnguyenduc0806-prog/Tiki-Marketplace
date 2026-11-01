"""
Crawl snapshot san pham Tiki theo ngay.

Cach dung:
    python crawl_tiki.py                  # dung CATEGORY_ID mac dinh
    python crawl_tiki.py 1591             # chi dinh category khac
    python crawl_tiki.py 1591 --probe     # chi tham do, khong crawl het

Moi lan chay sinh ra 2 file trong thu muc data/:
    raw/tiki_<cat>_<ngay>.json   - JSON tho, giu nguyen, de danh cuu minh sau nay
    tiki_<cat>_<ngay>.csv        - da parse, dung de phan tich

Chay 1 lan/ngay. Sau 6 tuan ban co chuoi thoi gian that.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

# ----------------------------------------------------------------
# Cau hinh
# ----------------------------------------------------------------

CATEGORY_ID = 1591           # cham soc toc va da dau
API_URL = "https://tiki.vn/api/personalish/v1/blocks/listings"
LIMIT = 40                   # so san pham moi trang
DELAY = 2.0                  # giay nghi giua cac request - DUNG GIAM
MAX_PAGES = 100              # chan tren, tranh vong lap vo han
TIMEOUT = 15

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
}

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"


# ----------------------------------------------------------------
# Lay du lieu
# ----------------------------------------------------------------

def fetch_page(category_id, page, retries=3):
    params = {"limit": LIMIT, "category": category_id, "page": page}
    for lan in range(retries):
        try:
            session = requests.Session()
            session.headers.update(HEADERS)
            r = session.get(API_URL, params=params, timeout=TIMEOUT)
            if r.status_code == 429:
                time.sleep(30)          # bị giới hạn tốc độ, nghỉ lâu
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if lan == retries - 1:
                raise
            time.sleep(5 * (lan + 1))   # chờ lâu dần: 5s, 10s


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
# Parse
# ----------------------------------------------------------------

def dig(obj, *path, default=None):
    """Lay gia tri long nhau an toan: dig(sp, 'quantity_sold', 'value')"""
    cur = obj
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
        if cur is None:
            return default
    return cur


def parse_item(sp: dict, crawled_at: str) -> dict:
    """
    Mot dong = mot san pham tai mot thoi diem.
    Moi truong deu dung .get() vi API co the thieu truong o vai san pham.
    """
    return {
        # --- dinh danh ---
        "product_id":    sp.get("id"),
        "sku":           sp.get("sku"),
        "name":          sp.get("name"),
        "url_key":       sp.get("url_key"),

        # --- gia: 3 truong nay la trai tim cua project ---
        "price":         sp.get("price"),          # gia dang ban
        "list_price":    sp.get("list_price"),     # gia goc niem yet
        "original_price": sp.get("original_price"),
        "discount":      sp.get("discount"),       # so tien giam
        "discount_rate": sp.get("discount_rate"),  # % giam

        # --- nguoi ban: phan ban hoi ---
        "seller_id":      sp.get("seller_id"),
        "seller_name":    sp.get("seller_name"),
        "seller_product_id": sp.get("seller_product_id"),
        "seller_type":    dig(sp, "seller", "type"),
        "is_official":    sp.get("official_store_name") is not None,
        "official_store_name": sp.get("official_store_name"),

        # --- thuong hieu ---
        "brand_id":      dig(sp, "brand", "id"),
        "brand_name":    sp.get("brand_name") or dig(sp, "brand", "name"),

        # --- tin hieu nhu cau ---
        "rating":        sp.get("rating_average"),
        "review_count":  sp.get("review_count"),
        "quantity_sold": dig(sp, "quantity_sold", "value"),

        # --- khac ---
        "is_freeship":   sp.get("freeship_campaign") is not None,
        "category_id":   CATEGORY_ID,

        # --- COT QUAN TRONG NHAT: bien snapshot thanh chuoi thoi gian ---
        "crawled_at":    crawled_at,
    }


# ----------------------------------------------------------------
# Chay
# ----------------------------------------------------------------

def crawl(category_id: int) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    crawled_at = now.strftime("%Y-%m-%d %H:%M:%S")
    day = now.strftime("%Y%m%d")

    raw_pages, rows = [], []
    seen_ids = set()

    for page in range(1, MAX_PAGES + 1):
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
            rows.append(parse_item(sp, crawled_at))
            moi += 1

        print(f"  trang {page}: {len(items)} dong, {moi} moi (tong {len(rows)})")

        last_page = dig(data, "paging", "last_page")
        if last_page and page >= last_page:
            break

        time.sleep(DELAY)

    if not rows:
        print("Khong lay duoc du lieu nao. Kiem tra lai category_id.")
        return

    # Luu tho TRUOC - neu sau nay phat hien thieu truong, van cuu duoc
    raw_path = RAW_DIR / f"tiki_{category_id}_{day}.json"
    raw_path.write_text(
        json.dumps(raw_pages, ensure_ascii=False), encoding="utf-8"
    )

    df = pd.DataFrame(rows)
    csv_path = DATA_DIR / f"tiki_{category_id}_{day}.csv"
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
    cat = int(args[0]) if args else CATEGORY_ID

    if "--probe" in sys.argv:
        probe(cat)
        return

    print(f"Crawl category {cat} - {datetime.now():%Y-%m-%d %H:%M}")
    crawl(cat)


if __name__ == "__main__":
    main()