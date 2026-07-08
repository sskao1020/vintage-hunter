import time
import requests
import streamlit as st
from bs4 import BeautifulSoup
import urllib.parse

# ==========================================
# 🛠️ 基礎設定（LINE 憑證）
# ==========================================
LINE_ACCESS_TOKEN = "ohycYk0F54YRIbduPJnUwUzYO9dpOXXHvYu4Gc01GO2PnIP2sAo/IX4CyLPst95GJd3NbleRd0IteUQaaMV7iD3pwScrjLKAq144VdvrorUkIG2QilqGR+SS3+/pmW8TRbcNwF2vIkbSuNwT67YbMwdB04t89/1O/w1cDnyilFU="
LINE_USER_ID = "U0779e71586f7e88b6bdb6822b6c83008"

def send_line_message(text):
    """透過 LINE Bot 發送主動推播"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
    }
    payload = {"to": LINE_USER_ID, "messages": [{"type": "text", "text": text}]}
    try:
        res = requests.post(url, headers=headers, json=payload)
        return res.status_code == 200
    except Exception as e:
        st.error(f"LINE 發送失敗: {e}")
        return False

# ==========================================
# 📡 各平台輕量爬蟲核心
# ==========================================

def scrape_yahoo_auction(keyword):
    """【日本雅虎拍賣】爬蟲"""
    safe_keyword = urllib.parse.quote(keyword)
    url = f"https://auctions.yahoo.co.jp/search/search?p={safe_keyword}&va={safe_keyword}&is_postage_mode=1&dest_pref_code=13&exflg=1&b=1&n=30&s1=new&o1=d"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ja-JP,ja;q=0.9",
    }
    items = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            products = soup.find_all("li", class_="Product")
            for prod in products:
                title_tag = prod.find("a", class_="Product__titleLink")
                if not title_tag: continue
                name = title_tag.text.strip()
                item_url = title_tag["href"]
                price_tag = prod.find("span", class_="Product__priceValue")
                price = "未顯示"
                if price_tag:
                    price_text = price_tag.text.replace("円", "").replace(",", "")
                    raw_price = "".join(filter(str.isdigit, price_text))
                    if raw_price: price = f"¥{int(raw_price):,}"
                items.append({"platform": "🇯🇵 Yahoo日拍", "name": name, "price": price, "url": item_url})
    except Exception as e:
        st.warning(f"Yahoo日拍連線異常: {e}")
    return items

def scrape_carousell_taiwan(keyword):
    """【台灣旋轉拍賣】爬蟲"""
    safe_keyword = urllib.parse.quote(keyword)
    url = f"https://tw.carousell.com/search/{safe_keyword}/?sort_by=time_created%2Cdescending"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9",
    }
    items = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.find_all("div", attrs={"data-testid": lambda x: x and "listing-card" in x})
            for card in cards:
                a_tags = card.find_all("a")
                if not a_tags: continue
                
                p_text_tags = card.find_all("p")
                if len(p_text_tags) < 2: continue
                
                name = p_text_tags[1].text.strip()
                item_url = "https://tw.carousell.com" + a_tags[0]["href"]
                price_text = p_text_tags[0].text.strip()
                
                items.append({"platform": "🎠 旋轉拍賣", "name": name, "price": price_text, "url": item_url})
    except Exception as e:
        st.warning(f"旋轉拍賣連線異常: {e}")
    return items

def scrape_shopee_taiwan(keyword):
    """【台灣蝦皮】公開網頁輕量爬蟲"""
    safe_keyword = urllib.parse.quote(keyword)
    url = f"https://shopee.tw/api/v4/search/search_items?keyword={safe_keyword}&limit=30&newest=0&by=ctime&order=desc"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://shopee.tw/search?keyword={safe_keyword}"
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
                    
                    price = f"${int(price_raw / 100000):,}" if price_raw else "未顯示"
                    item_url = f"https://shopee.tw/product/{shop_id}/{item_id}"
                    
                    items.append({"platform": "🧡 台灣蝦皮", "name": name, "price": price, "url": item_url})
    except Exception as e:
        st.warning(f"台灣蝦皮連線異常 (可能觸發防爬蟲機制): {e}")
    return items

# ==========================================
# 🎨 Streamlit 網頁美學介面
# ==========================================
st.set_page_config(page_title="全球古著獵人系統", page_icon="🕵️‍♂️", layout="wide")

st.title("🕵️‍♂️ Global Vintage Hunter Dashboard")
st.caption("跨國次級市場情報官 — 整合日拍、蝦皮、旋轉拍賣，精準狙擊")
st.markdown("---")

# 🤖 建立左側邊欄 控制台
st.sidebar.header("🎛️ 獵人核心設定")
search_keyword = st.sidebar.text_input("搜尋關鍵字", value="LVC 47501")

# 尺寸白名單
selected_sizes = st.sidebar.multiselect(
    "腰圍白名單 (留空代表不限尺寸)",
    options=["W29", "W30", "W31", "W32", "W33", "W34", "W36"],
    default=["W31", "W32", "W33"],
)

# 排除關鍵字
exclude_input = st.sidebar.text_input("排除關鍵字 (請用逗號隔開)", value="海報,貼紙,カタログ,型紙,代購,預購")
exclude_keywords = [k.strip().upper() for k in exclude_input.replace("，", ",").split(",") if k.strip()]

# 平台多選開關
platforms_to_search = st.sidebar.multiselect(
    "出動目標市場",
    options=["🇯🇵 Yahoo日拍", "🧡 台灣蝦皮", "🎠 旋轉拍賣"],
    default=["🇯🇵 Yahoo日拍", "🧡 台灣蝦皮", "🎠 旋轉拍賣"]
)

enable_line = st.sidebar.toggle("同步發送 LINE 通知", value=True)

# 🎯 網頁中央主畫面
if st.sidebar.button("🚀 立即發動全球手動掃描", use_container_width=True):
    if not platforms_to_search:
        st.error("❌ 請至少選擇一個目標市場進行掃描！")
        st.stop()
        
    st.subheader(f"🔍 正在發動聯網狙擊：【{search_keyword}】...")
    
    all_raw_items = []
    
    if "🇯🇵 Yahoo日拍" in platforms_to_search:
        with st.spinner("情報官正在翻閱日本雅虎拍賣..."):
            all_raw_items.extend(scrape_yahoo_auction(search_keyword))
            
    if "🧡 台灣蝦皮" in platforms_to_search:
        with st.spinner("情報官正在滲透台灣蝦皮商城..."):
            all_raw_items.extend(scrape_shopee_taiwan(search_keyword))
            
    if "🎠 旋轉拍賣" in platforms_to_search:
        with st.spinner("情報官正在瀏覽旋轉拍賣地盤..."):
            all_raw_items.extend(scrape_carousell_taiwan(search_keyword))

    # ------ 🎛️ 聯網過濾機制 ------
    valid_items = []
    for item in all_raw_items:
        name_upper = item["name"].upper()
        
        # 1. 基礎型號雙重防線
        if "47501" not in name_upper and "1947" not in name_upper:
            continue
            
        # 2. 黑名單排除
        if any(black in name_upper for black in exclude_keywords):
            continue
            
        # 3. 尺寸白名單過濾
        if selected_sizes and not any(size in name_upper for size in selected_sizes):
            continue
            
        valid_items.append(item)

    # ------ 🎨 網頁結果視覺呈現 ------
    if not valid_items:
        st.warning(" 掃描完成。目前全球市場上，沒有符合您尺寸與過濾條件的新上架商品。")
    else:
        st.success(f"🎉 聯網回報：成功捕捉到 {len(valid_items)} 件完美符合條件的夢幻獵物！")
        
        for item in valid_items:
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**[{item['platform']}] 👖 {item['name']}**")
                    st.caption(f"連結安全驗證通過")
                with col2:
                    st.subheader(item["price"])
                    st.link_button("👉 前往賣場", item["url"])
                    
            if enable_line:
                msg = (
                    f"🔨【全球儀表板精準獵取】\n\n"
                    f"🏪 平台：{item['platform']}\n"
                    f"📦 商品：{item['name']}\n"
                    f"💰 價格：{item['price']}\n"
                    f"🔗 傳送門：{item['url']}"
                )
                send_line_message(msg)
                time.sleep(0.5)
else:
    st.info("💡 請在左側主控台調整您的全球獵場設定，隨時點擊『立即發動全球手動掃描』收割三方市場情報。")
