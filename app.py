def scrape_shopee_taiwan(keyword):
    """【台灣蝦皮】公開網頁輕量爬蟲"""
    import urllib.parse
    
    # 關鍵字安全編碼：將中文轉換為瀏覽器通用的 % 編碼，防止 latin-1 編碼錯誤
    safe_keyword = urllib.parse.quote(keyword)
    
    # 蝦皮防爬蟲極嚴格，此處採用其公開的不需驗證後台 API 節點進行關鍵字請求
    url = f"https://shopee.tw/api/v4/search/search_items?keyword={safe_keyword}&limit=30&newest=0&by=ctime&order=desc"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://shopee.tw/search?keyword={safe_keyword}" # 這裡也使用了安全編碼
    }
    items = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if "items" in data and data["items"]:
                for raw_item in data["items"]:
                    item_basic = raw_item.get("item_basic")
                    if not item_basic: continue
                    
                    name = item_basic.get("name")
                    item_id = item_basic.get("itemid")
                    shop_id = item_basic.get("shopid")
                    price_raw = item_basic.get("price")
                    
                    # 蝦皮 API 價格通常會放大 100,000 倍，需進行換算
                    price = f"${int(price_raw / 100000):,}" if price_raw else "未顯示"
                    item_url = f"https://shopee.tw/product/{shop_id}/{item_id}"
                    
                    items.append({"platform": "🧡 台灣蝦皮", "name": name, "price": price, "url": item_url})
    except Exception as e:
        st.warning(f"台灣蝦皮連線異常 (可能觸發防爬蟲機制): {e}")
    return items
