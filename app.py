import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import io
from datetime import datetime

# ── 頁面設定 ─────────────────────────────────────────────
st.set_page_config(page_title="資產再平衡系統", page_icon="📊", layout="centered")

# ── 自定義 CSS ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }
.metric-card { background: #1e2230; border-radius: 12px; padding: 16px 20px; border-left: 4px solid #4fd1c5; }
</style>
""", unsafe_allow_html=True)

# ── 設定與連線 ──────────────────────────────────────────────
TARGETS = {"美股大類": 50, "台股": 30, "現金": 10, "虛擬貨幣": 10}
conn = st.connection("gsheets", type=GSheetsConnection)

# ── 匯率功能 ────────────────────────────────────────────
@st.cache_data(ttl=1800)
def fetch_usd_rate():
    try:
        url = "https://rate.bot.com.tw/xrt/flcsv/0/day"
        r = requests.get(url, timeout=8)
        r.encoding = "utf-8"
        df = pd.read_csv(io.StringIO(r.text), header=None)
        row = df[df[0].astype(str).str.contains("USD", na=False)]
        if not row.empty: return float(row.iloc[0, 13]), None
    except Exception as e: return None, str(e)
    return None, "無法取得匯率"

# ── 主界面 ──────────────────────────────────────────────────
st.title("📊 資產再平衡指揮中心")

auto_rate, err = fetch_usd_rate()
usd_rate = st.number_input("💵 當前美金匯率", value=auto_rate if auto_rate else 32.5, step=0.01)

st.divider()

# 帳戶輸入
st.subheader("🏦 帳戶資產輸入")
col1, col2 = st.columns(2)
with col1:
    twd_cash   = st.number_input("🏦 台幣現金 (TWD)", min_value=0, step=10000)
    tw_stock   = st.number_input("📈 台股總額 (TWD)", min_value=0, step=10000)
    crypto_twd = st.number_input("₿ 虛擬貨幣-台幣帳戶 (TWD)", min_value=0, step=1000)
with col2:
    sub_broker = st.number_input("🌐 複委託 (USD)",   min_value=0, step=100)
    us_stock   = st.number_input("🇺🇸 海外美股 (USD)", min_value=0, step=100)
    crypto_usd = st.number_input("₿ 虛擬貨幣-美金帳戶 (USDT)", min_value=0, step=100)

st.divider()

# 容忍區間
st.subheader("⚙️ 容忍區間設定 (±%)")
c1, c2, c3, c4 = st.columns(4)
tol_us = c1.number_input("美股", 1, 20, 5)
tol_tw = c2.number_input("台股", 1, 20, 5)
tol_cash = c3.number_input("現金", 1, 20, 8)
tol_crypto = c4.number_input("虛幣", 1, 20, 3)
tols = {"美股大類": tol_us, "台股": tol_tw, "現金": tol_cash, "虛擬貨幣": tol_crypto}

# ── 分析與同步 ──────────────────────────────────────────
if st.button("🔍 開始分析並同步至雲端", type="primary", use_container_width=True):
    us_twd = (sub_broker + us_stock) * usd_rate
    crypto_total_twd = (crypto_usd * usd_rate) + crypto_twd
    total = twd_cash + tw_stock + us_twd + crypto_total_twd

    if total > 0:
        actual_pcts = {
            "美股大類": us_twd / total * 100,
            "台股": tw_stock / total * 100,
            "現金": twd_cash / total * 100,
            "虛擬貨幣": crypto_total_twd / total * 100
        }
        
        st.metric("總資產估值", f"NT$ {total:,.0f}")

        # 準備要同步的資料（嚴格對應表頭）
        save_data = {
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Total": float(total),
            "USD_Rate": float(usd_rate),
            "US_Stock_Pct": round(actual_pcts["美股大類"], 2),
            "TW_Stock_Pct": round(actual_pcts["台股"], 2),
            "Cash_Pct": round(actual_pcts["現金"], 2),
            "Crypto_Pct": round(actual_pcts["虛擬貨幣"], 2)
        }

        try:
            # 讀取並更新
            df = conn.read(ttl=0)
            # 確保新資料與舊資料欄位順序一致
            new_row = pd.DataFrame([save_data])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(data=updated_df)
            st.success("✅ 同步成功！資料已寫入 Google Sheets。")
        except Exception as e:
            st.error(f"❌ 同步失敗：{e}")

        # 顯示簡易圖表
        st.bar_chart(pd.DataFrame(actual_pcts.items(), columns=['類別', '比例']).set_index('類別'), color="#4fd1c5", horizontal=True)

# ── 歷史紀錄趨勢 ─────────────────────────────────────────
st.divider()
st.subheader("📁 雲端歷史趨勢")
try:
    history_df = conn.read(ttl=0)
    if not history_df.empty:
        st.dataframe(history_df.tail(5), use_container_width=True)
        st.line_chart(history_df.set_index("Date")["Total"], color="#4fd1c5")
except:
    st.info("尚未偵測到歷史紀錄。")
