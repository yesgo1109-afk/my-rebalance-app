import streamlit as st
import pandas as pd
import requests
import io
import os
from datetime import datetime

# ── 頁面設定 ─────────────────────────────────────────────
st.set_page_config(page_title="資產再平衡系統", page_icon="📊", layout="centered")

# 歷史紀錄檔案名稱
HISTORY_FILE = "asset_history.csv"

# ── 再平衡目標比例 (TARGETS) ───────────────────────────────────
# 您可以隨時在這裡修改您的黃金比例
TARGETS = {"美股大類": 50, "台股": 30, "現金": 10, "虛擬貨幣": 10}

# ── 數據處理功能 ──────────────────────────────────────────
def load_data():
    if os.path.exists(HISTORY_FILE):
        return pd.read_csv(HISTORY_FILE)
    return pd.DataFrame(columns=["Date", "Total", "USD_Rate", "US_Stock_Pct", "TW_Stock_Pct", "Cash_Pct", "Crypto_Pct"])

def save_data(new_row_dict):
    df = load_data()
    new_row = pd.DataFrame([new_row_dict])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(HISTORY_FILE, index=False)

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
auto_rate, _ = fetch_usd_rate()
usd_rate = st.number_input("💵 當前美金匯率", value=auto_rate if auto_rate else 32.5, step=0.01)

st.divider()

# 1. 帳戶輸入
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

# 2. 容忍區間設定 (補回這部分)
st.subheader("⚙️ 容忍區間設定 (±%)")
c1, c2, c3, c4 = st.columns(4)
tol_us = c1.number_input("美股", 1, 20, 5)
tol_tw = c2.number_input("台股", 1, 20, 5)
tol_cash = c3.number_input("現金", 1, 20, 8)
tol_crypto = c4.number_input("虛幣", 1, 20, 3)
tols = {"美股大類": tol_us, "台股": tol_tw, "現金": tol_cash, "虛擬貨幣": tol_crypto}

# 3. 分析按鈕
if st.button("🔍 開始分析並儲存紀錄", type="primary", use_container_width=True):
    us_twd = (sub_broker + us_stock) * usd_rate
    crypto_total_twd = (crypto_usd * usd_rate) + crypto_twd
    total = twd_cash + tw_stock + us_twd + crypto_total_twd

    if total > 0:
        # 計算實際比例
        actual_pcts = {
            "美股大類": us_twd / total * 100,
            "台股": tw_stock / total * 100,
            "現金": twd_cash / total * 100,
            "虛擬貨幣": crypto_total_twd / total * 100
        }
        
        st.divider()
        st.header(f"總資產估值：NT$ {total:,.0f}")

        # 顯示各類別詳細分析與建議
        st.subheader("📋 建議操作建議")
        for cat, target in TARGETS.items():
            pct = actual_pcts[cat]
            diff = pct - target
            is_ok = abs(diff) <= tols[cat]
            
            # 狀態顯示
            status_icon = "✅" if is_ok else "⚠️"
            with st.expander(f"{status_icon} {cat}: 目前 {pct:.1f}% (目標 {target}%)"):
                st.write(f"偏離幅度: {diff:+.1f}%")
                if not is_ok:
                    gap_twd = abs(diff / 100 * total)
                    action = "賣出" if diff > 0 else "加碼"
                    
                    if "美股" in cat:
                        st.warning(f"💡 建議 {action} 約 {gap_twd / usd_rate:,.0f} USD")
                    elif "虛擬貨幣" in cat:
                        st.warning(f"💡 建議 {action} 約 {gap_twd / usd_rate:,.0f} USDT")
                    else:
                        st.warning(f"💡 建議 {action} 約 NT$ {gap_twd:,.0f}")

        # 存檔動作
        save_data({
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Total": total,
            "USD_Rate": usd_rate,
            "US_Stock_Pct": round(actual_pcts["美股大類"], 2),
            "TW_Stock_Pct": round(actual_pcts["台股"], 2),
            "Cash_Pct": round(actual_pcts["現金"], 2),
            "Crypto_Pct": round(actual_pcts["虛擬貨幣"], 2)
        })
        st.success("✅ 數據分析完成且已存檔")

        # 圖表顯示
        st.bar_chart(pd.DataFrame(actual_pcts.items(), columns=['類別', '比例']).set_index('類別'), color="#4fd1c5", horizontal=True)

# ── 歷史紀錄趨勢 ─────────────────────────────────────────
st.divider()
st.subheader("📁 歷史趨勢紀錄")
history_df = load_data()
if not history_df.empty:
    st.dataframe(history_df.tail(10), use_container_width=True)
    st.line_chart(history_df.set_index("Date")["Total"], color="#4fd1c5")
    
    # 下載按鈕
    csv = history_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 下載完整 CSV 備份", data=csv, file_name="asset_history.csv", mime="text/csv")
