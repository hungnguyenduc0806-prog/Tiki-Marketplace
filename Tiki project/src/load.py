"""
Do CSV da parse vao bang prices trong PostgreSQL.

Cach dung (tu thu muc goc):
    python -m src.load                      # do file cua hom nay
    python -m src.load 20261031             # do mot ngay cu the
    python -m src.load --all                # do lai toan bo thu muc processed

Ghi theo kieu UPSERT: khoa chinh la (product_id, crawled_date), nen chay lai
cung mot ngay khong tao dong trung - chi cap nhat gia tri moi. Day goi la
idempotent, va no la ly do script nay chay lai bao nhieu lan cung an toan.
"""

import sys
from datetime import datetime

import pandas as pd
from psycopg2.extras import execute_values

import config
from src.db import get_conn

COLUMNS = [
    "product_id", "crawled_date", "sku", "name",
    "price", "list_price", "original_price", "discount", "discount_rate",
    "seller_id", "seller_name", "is_official",
    "brand_id", "brand_name",
    "rating", "review_count", "quantity_sold",
    "category_id",
]

UPSERT = f"""
INSERT INTO prices ({", ".join(COLUMNS)})
VALUES %s
ON CONFLICT (product_id, crawled_date) DO UPDATE SET
    price         = EXCLUDED.price,
    list_price    = EXCLUDED.list_price,
    discount_rate = EXCLUDED.discount_rate,
    rating        = EXCLUDED.rating,
    review_count  = EXCLUDED.review_count,
    quantity_sold = EXCLUDED.quantity_sold;
"""


def load_csv(path) -> int:
    df = pd.read_csv(path)
    df["crawled_date"] = pd.to_datetime(df["crawled_at"]).dt.date

    # Mot san pham chi duoc xuat hien mot lan trong mot ngay
    df = df.drop_duplicates(subset=["product_id", "crawled_date"], keep="last")

    df = df.reindex(columns=COLUMNS)
    rows = [tuple(None if pd.isna(v) else v for v in r)
            for r in df.itertuples(index=False, name=None)]

    with get_conn() as conn, conn.cursor() as cur:
        execute_values(cur, UPSERT, rows, page_size=500)

    print(f"  {path.name}: {len(rows)} dong")
    return len(rows)


def main():
    if "--all" in sys.argv:
        files = sorted(config.PROCESSED_DIR.glob("tiki_*.csv"))
    else:
        args = [a for a in sys.argv[1:] if not a.startswith("--")]
        day = args[0] if args else datetime.now().strftime("%Y%m%d")
        files = [config.PROCESSED_DIR / f"tiki_{config.CATEGORY_ID}_{day}.csv"]

    tong = 0
    for f in files:
        if not f.exists():
            print(f"  khong thay {f}")
            continue
        tong += load_csv(f)

    print(f"Tong cong {tong} dong vao bang prices")


if __name__ == "__main__":
    main()
