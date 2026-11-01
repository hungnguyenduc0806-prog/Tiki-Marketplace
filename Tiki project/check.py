import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}
url = "https://tiki.vn/api/personalish/v1/blocks/listings"
params = {"limit": 40, "category": 1591, "page": 1}

r = requests.get(url, params=params, headers=HEADERS, timeout=15)
data = r.json()

print("Tổng sản phẩm:", data.get("paging", {}).get("total"))
print("Số trang:", data.get("paging", {}).get("last_page"))
print("Số dòng trang 1:", len(data.get("data", [])))

# Xem thử một sản phẩm có những trường gì
import json
print(json.dumps(data["data"][0], ensure_ascii=False, indent=2)[:2000])