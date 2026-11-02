def dig(obj, *path, default=None):
    cur = obj
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
        if cur is None:
            return default
    return cur

def parse_item(sp: dict, crawled_at: str, category_id: int) -> dict:
    return {
        "product_id":    sp.get("id"),
        "sku":           sp.get("sku"),
        "name":          sp.get("name"),
        "url_key":       sp.get("url_key"),

        "price":          sp.get("price"),
        "list_price":     sp.get("list_price"),
        "original_price": sp.get("original_price"),
        "discount":       sp.get("discount"),
        "discount_rate":  sp.get("discount_rate"),

        "seller_id":           sp.get("seller_id"),
        "seller_name":         sp.get("seller_name"),
        "seller_product_id":   sp.get("seller_product_id"),
        "seller_type":         dig(sp, "seller", "type"),
        "is_official":         sp.get("official_store_name") is not None,
        "official_store_name": sp.get("official_store_name"),

        "brand_id":   dig(sp, "brand", "id"),
        "brand_name": sp.get("brand_name") or dig(sp, "brand", "name"),

        "rating":        sp.get("rating_average"),
        "review_count":  sp.get("review_count"),
        "quantity_sold": dig(sp, "quantity_sold", "value"),

        "is_freeship": sp.get("freeship_campaign") is not None,
        "category_id": category_id,

        "crawled_at": crawled_at,
    }
