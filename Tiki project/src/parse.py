"""
Bien mot san pham tho tu API thanh mot dong du lieu phang.

Tach rieng khoi crawl.py de co the test ma khong can goi mang.
"""


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


def parse_item(sp: dict, crawled_at: str, category_id: int) -> dict:
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
        "price":          sp.get("price"),           # gia dang ban
        "list_price":     sp.get("list_price"),      # gia goc niem yet
        "original_price": sp.get("original_price"),
        "discount":       sp.get("discount"),        # so tien giam
        "discount_rate":  sp.get("discount_rate"),   # % giam

        # --- nguoi ban: phan ban hoi ---
        "seller_id":           sp.get("seller_id"),
        "seller_name":         sp.get("seller_name"),
        "seller_product_id":   sp.get("seller_product_id"),
        "seller_type":         dig(sp, "seller", "type"),
        "is_official":         sp.get("official_store_name") is not None,
        "official_store_name": sp.get("official_store_name"),

        # --- thuong hieu ---
        "brand_id":   dig(sp, "brand", "id"),
        "brand_name": sp.get("brand_name") or dig(sp, "brand", "name"),

        # --- tin hieu nhu cau ---
        "rating":        sp.get("rating_average"),
        "review_count":  sp.get("review_count"),
        "quantity_sold": dig(sp, "quantity_sold", "value"),

        # --- khac ---
        "is_freeship": sp.get("freeship_campaign") is not None,
        "category_id": category_id,

        # --- COT QUAN TRONG NHAT: bien snapshot thanh chuoi thoi gian ---
        "crawled_at": crawled_at,
    }
