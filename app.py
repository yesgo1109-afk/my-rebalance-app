import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import io
from datetime import datetime

# ── 頁面設定 ─────────────────────────────────────────────
st.set_page_config(
    page_title="資產再平衡系統",
    page_icon="📊",
    layout="centered",
)

# ── 自定義 CSS（維持您原本喜歡的風格） ───────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }
.metric-card {
    background: #1e2230;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 10px;
    border-left: 4px solid #4fd1c5;
}
.action-box {
    background: rgba(246,173,85,0.1);
    border-left: 3px solid #f6ad55;
    border-radius: 6px;
    padding: 8px 12px;
    margin-top: 8px;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# ── 設定與連線 ──────────────────────────────────────────────
TARGETS = {"美股大類": 50, "台股": 25, "現金": 15, "虛擬貨幣": 10}
COLORS  = ["#4fd1c5", "#90cdf4", "#68d391", "#f6ad55"]

# 初始化 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

# ── 匯率抓取功能 ────────────────────────────────────────────
@st.cache_data(ttl=1800)
def fetch_usd_rate():
    try:
        url = "https://rate.bot.com.tw/xrt/flcsv/0/day"
        r = requests.get(url, timeout=8)
        r.encoding = "utf-8"
        df = pd.read_csv(io.StringIO(r.text), header=None)
        row = df[df[0].astype(str).str.contains("USD", na=False)]
        if not row.empty:
            sell = float(row.iloc[0, 13])
            return sell, None
    except Exception as e:
        return None, str(e)
    return None, "找不到數據"

# ── 主界面 ──────────────────────────────────────────────────
st.title("📊 資產再平衡指揮中心")
st.caption("同步雲端版 · 自動化分析")

# 匯率區
auto_rate, err = fetch_usd_rate()
usd_rate = st.number_input("💵 當前美金匯率 (台銀即期)", value=auto_rate if auto_rate else 32.5, step=0.01)

st.divider()

# 帳戶輸入
st.subheader("🏦 帳戶資產輸入")
col1, col2 = st.columns(2)
with col1:
    twd_cash   = st.number_input("🏦 台幣現金 (TWD)", min_value=0, step=10000)
    tw_stock   = st.number_input("📈 台股總額 (TWD)", min_value=0, step=10000)
with col2:
    sub_broker = st.number_input("🌐 複委託 (USD)",   min_value=0, step=100)
    us_stock   = st.number_input("🇺🇸 海外美股 (USD)", min_value=0, step=100)
    crypto     = st.number_input("₿ 虛擬貨幣 (USDT)", min_value=0, step=100)

st.divider()

# 容忍區間
st.subheader("⚙️ 容忍區間設定（±%）")
c1, c2, c3, c4 = st.columns(4)
tol_us = c1.number_input("美股", 1, 20, 5)
tol_tw = c2.number_input("台股", 1, 20, 5)
tol_cash = c3.number_input("現金", 1, 20, 8)
tol_crypto = c4.number_input("虛幣", 1, 20, 3)
tols = {"美股大類": tol_us, "台股": tol_tw, "現金": tol_cash, "虛擬貨幣": tol_crypto}

# ── 開始分析與存檔 ──────────────────────────────────────────
if st.button("🔍 開始分析並同步至雲端", type="primary", use_container_width=True):
    us_twd = (sub_broker + us_stock) * usd_rate
    crypto_twd = crypto * usd_rate
    total = twd_cash + tw_stock + us_twd + crypto_twd

    if total == 0:
        st.error("請輸入資產金額")
    else:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        actual_pcts = {
            "美股大類": us_twd / total * 100,
            "台股": tw_stock / total * 100,
            "現金": twd_cash / total * 100,
            "虛擬貨幣": crypto_twd / total * 100
        }

        # 顯示總結果
        st.metric("總資產（台幣估值）", f"NT$ {total:,.0f}")
        
        # 準備存檔數據
        new_data = {
            "Date": now_str,
            "Total": total,
            "USD_Rate": usd_rate,
            "US_Stock_Pct": round(actual_pcts["美股大類"], 2),
            "TW_Stock_Pct": round(actual_pcts["台股"], 2),
            "Cash_Pct": round(actual_pcts["現金"], 2),
            "Crypto_Pct": round(actual_pcts["虛擬貨幣"], 2)
        }

        # 寫入 Google Sheets
        try:
            existing_df = conn.read(ttl=0)
            updated_df = pd.concat([existing_df, pd.DataFrame([new_data])], ignore_index=True)
            conn.update(data=updated_df)
            st.success("✅ 數據已成功同步至 Google Sheets 歷史紀錄")
        except Exception as e:
            st.error(f"❌ 雲端同步失敗：{e}")

        # 顯示圖表
        chart_df = pd.DataFrame({"類別": list(actual_pcts.keys()), "比例": list(actual_pcts.values())})
        st.bar_chart(chart_df.set_index("類別"), color="#4fd1c5", horizontal=True)

        # 各類別分析
        for cat, target in TARGETS.items():
            pct = actual_pcts[cat]
            diff = pct - target
            is_ok = abs(diff) <= tols[cat]
            status = "✅ 正常" if is_ok else "⚠️ 需調整"
            
            with st.expander(f"{status} {cat}: {pct:.1f}% (目標 {target}%)"):
                st.write(f"目前偏離: {diff:+.1f}%")
                if not is_ok:
                    gap = abs(diff / 100 * total)
                    action = "賣出" if diff > 0 else "加碼"
                    unit = "USD" if "美股" in cat or "虛幣" in cat else "TWD"
                    val = gap / usd_rate if unit != "TWD" else gap
                    st.warning(f"💡 建議 {action} 約 {val:,.0f} {unit}")

# ── 顯示歷史紀錄（從 Google Sheets 讀取） ─────────────────────────
st.divider()
st.subheader("📁 雲端歷史趨勢")
try:
    history_df = conn.read(ttl=0)
    if not history_df.empty:
        st.dataframe(history_df.tail(10), use_container_width=True)
        st.line_chart(history_df.set_index("Date")["Total"], color="#4fd1c5")
    else:
        st.caption("尚無雲端紀錄。")
except:
    st.caption("連線至 Google Sheets 中...")
