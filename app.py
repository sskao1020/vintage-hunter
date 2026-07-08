import time
import requests
import streamlit as st
from bs4 import BeautifulSoup

# ==========================================
# 🛠️ 基礎設定（已直接寫入你的 LINE 憑證）
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
# 🎨 Streamlit 網頁美學介面
# ==========================================
# 設定網頁標題、分頁圖示與寬螢幕佈局
st.set_page_config(page_title="次級市場獵人系統", page_icon="🕵️‍♂️", layout="wide")

# 主畫面大標題
st.title("🕵️‍♂️ Vintage Hunter Dashboard")
st.caption("專屬你的個人次級市場情報官 — 內斂、精準、自動化")
st.markdown("---")

# 🤖 建立左側邊欄 (Sidebar) 控制台
st.sidebar.header("🎛️ 獵人核心設定")

# 1. 搜尋關鍵字輸入
search_keyword = st.sidebar.text_input("搜尋關鍵字", value="LVC 47501")

# 2. 尺寸白名單 (多選標籤)
selected_sizes = st.sidebar.multiselect(
    "腰圍白名單 (留空代表不限尺寸)",
    options=["W29", "W30", "W31", "W32", "W33", "W34", "W36"],
    default=["W31", "W32", "W33"],
)

# 3. 排除關鍵字（用英文或中文逗號隔開皆可）
exclude_input = st.sidebar.text_input(
    "排除關鍵字 (請用逗號隔開)", value="海報,貼紙,カタログ,型紙"
)
# 將輸入的黑名單轉為列表並清理空白，同時轉換為大寫方便後續比對
exclude_keywords = [
    k.strip().upper() for k in exclude_input.replace("，", ",").split(",") if k.strip()
]

# 4. 同步通知開關
enable_line = st.sidebar.toggle("同步發送 LINE 通知", value=True)

# 🎯 網頁中央主畫面：手動啟動按鈕
if st.sidebar.button("🚀 立即出動手動掃描", use_container_width=True):
    st.subheader(f"🔍 正在掃描 Yahoo 拍賣： {search_keyword}...")

    # 動態產生 Yahoo 拍賣網址（由新到舊排序、販售中）
    yahoo_url = f"https://auctions.yahoo.co.jp/search/search?p={search_keyword}&va={search_keyword}&is_postage_mode=1&dest_pref_code=13&exflg=1&b=1&n=50&s1=new&o1=d"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ja-JP,ja;q=0.9",
    }

    # 顯示優雅的進度載入動畫
    with st.spinner("情報官正在翻閱日本雅虎拍賣..."):
        try:
            res = requests.get(yahoo_url, headers=headers, timeout=15)
            if res.status_code != 200:
                st.error(f"日拍伺服器請求失敗，狀態碼: {res.status_code}")
                st.stop()

            soup = BeautifulSoup(res.text, "html.parser")
            products = soup.find_all("li", class_="Product")

            valid_items = []
            for prod in products:
                title_tag = prod.find("a", class_="Product__titleLink")
                if not title_tag:
                    continue

                name = title_tag.text.strip()
                item_url = title_tag["href"]
                item_id = item_url.split("/")[-1].split("?")[0]

                price_tag = prod.find("span", class_="Product__priceValue")
                price = "??"
                if price_tag:
                    price_text = price_tag.text.replace("円", "").replace(
                        ",", ""
                    )
                    price = "".join(filter(str.isdigit, price_text))

                # ------ 🎛️ 嚴格情報過濾機制 ------
                name_upper = name.upper()

                # 1. 基礎型號雙重防線
                if "47501" not in name_upper and "1947" not in name_upper:
                    continue

                # 2. 黑名單排除
                if any(black in name_upper for black in exclude_keywords):
                    continue

                # 3. 尺寸白名單過濾
                if selected_sizes and not any(
                    size in name_upper for size in selected_sizes
                ):
                    continue

                valid_items.append(
                    {"id": item_id, "name": name, "price": price, "url": item_url}
                )

            # ------ 🎨 網頁結果視覺呈現 ------
            if not valid_items:
                st.warning(" 掃描完成。很遺憾，當前畫面上沒有符合尺寸與過濾條件的新上架商品。")
            else:
                st.success(
                    f"🎉 成功捕捉到 {len(valid_items)} 件完美符合條件的 LVC 獵物！"
                )

                # 以極簡現代的容器卡片排版呈現
                for item in valid_items:
                    display_price = (
                        f"¥{int(item['price']):,}"
                        if item["price"].isdigit()
                        else "未顯示"
                    )

                    # 建立美觀的無邊框橫向區塊
                    with st.container(border=True):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"**👖 {item['name']}**")
                            st.caption(f"商品 ID: {item['id']}")
                        with col2:
                            st.subheader(display_price)
                            st.link_button("👉 前往日拍", item["url"])

                    # 如果有開啟 LINE 同步，且確實是精準情報，則發送通知
                    if enable_line:
                        msg = (
                            f"🔨【儀表板精準獵取】\n\n"
                            f"📦 商品：{item['name']}\n"
                            f"💰 價格：{display_price}\n"
                            f"🔗 傳送門：{item['url']}"
                        )
                        send_line_message(msg)
                        time.sleep(0.5)  # 微幅延遲，確保 LINE 接收順暢

        except Exception as e:
            st.error(f"系統核心執行發生錯誤: {e}")
else:
    # 預設無按鈕觸發時的質感留白畫面
    st.info(
        "💡 請在左側主控台優雅地勾選你的腰圍與設定排除詞，隨時點擊『立即出動手動掃描』即可收割即時情報。"
    )
