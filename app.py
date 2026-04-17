import streamlit as st
import pandas as pd
import requests
import io
import csv
import plotly.graph_objects as go
from datetime import datetime

# 頁面配置
st.set_page_config(page_title="資產再平衡系統", page_icon="📊", layout="wide")

# 自定義 CSS 讓介面更接近原本的 HTML 風格
st.markdown("""
    <style>
    .main { background-color: #0d0f14; color: #e2e8f0; }
    .stNumberInput { background-color: #161920; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 資產再平衡指揮中心")
st.caption("積極中帶保守 · 自動化分析")

# 1. 自動抓取台銀匯率
@st.cache_data(ttl=3600)
def get_usd_rate():
    try:
        url = "https://rate.bot.com.tw/xrt/flcsv/0/day"
        response = requests.get(url)
        response.encoding = 'utf-8'
        f = io.StringIO(response.text)
        reader = csv.reader(f)
        for row in reader:
            if 'USD' in row[0]: return float(row[13])
        return 32.5
    except: return 32.5

usd_rate = get_usd_rate()
st.sidebar.metric("今日美金匯率 (台銀即期)", f"{usd_rate} TWD")

# 2. 帳戶資產輸入
st.header("1. 帳戶資產輸入")
col1, col2, col3 = st.columns(3)

with col1:
    twd_cash = st.number_input("台幣現金 (TWD)", min_value=0, value=0, step=1000)
    tw_stock = st.number_input("台股總額 (TWD)", min_value=0, value=0, step=1000)
with col2:
    sub_broker = st.number_input("複委託 (USD)", min_value=0, value=0, step=100)
    us_stock = st.number_input("海外美股 (USD)", min_value=0, value=0, step=100)
with col3:
    crypto_usdt = st.number_input("虛擬貨幣 (USDT)", min_value=0, value=0, step=100)

# 3. 容忍區間設定 (原本 HTML 的功能)
st.header("2. 容忍區間設定 (±%)")
t_col1, t_col2, t_col3, t_col4 = st.columns(4)
with t_col1: tol_us = st.slider("美股容忍", 1, 10, 5)
with t_col2: tol_tw = st.slider("台股容忍", 1, 10, 5)
with t_col3: tol_cash = st.slider("現金容忍", 1, 15, 8)
with t_col4: tol_crypto = st.slider("虛幣容忍", 1, 10, 3)

# 4. 計算邏輯
us_total_twd = (sub_broker + us_stock) * usd_rate
crypto_total_twd = crypto_usdt * usd_rate
total_assets = twd_cash + tw_stock + us_total_twd + crypto_total_twd

# 目標比例
TARGETS = {"美股類別": 0.50, "台股": 0.25, "現金": 0.15, "虛擬貨幣": 0.10}
TOLS = {"美股類別": tol_us, "台股": tol_tw, "現金": tol_cash, "虛擬貨幣": tol_crypto}
actual_vals = {"美股類別": us_total_twd, "台股": tw_stock, "現金": twd_cash, "虛擬貨幣": crypto_total_twd}

if total_assets > 0:
    st.divider()
    st.header(f"總資產估值：NT$ {total_assets:,.0f}")

    # 圓餅圖 (補回 UI 美感)
    fig = go.Figure(data=[go.Pie(labels=list(actual_vals.keys()), 
                                 values=list(actual_vals.values()), 
                                 hole=.4,
                                 marker_colors=['#4fd1c5', '#90cdf4', '#68d391', '#f6ad55'])])
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
    st.plotly_chart(fig)

    # 5. 分析結果與建議操作 (核心功能)
    st.header("3. 建議操作順序")
    analysis_data = []
    priority_list = []

    for name, target_pct in TARGETS.items():
        actual_pct = actual_vals[name] / total_assets
        diff_pct = (actual_pct - target_pct) * 100
        diff_twd = (total_assets * target_pct) - actual_vals[name]
        
        status = "✅ 正常" if abs(diff_pct) <= TOLS[name] else "⚠️ 需調整"
        
        if status == "⚠️ 需調整":
            dir_text = "減碼" if diff_pct > 0 else "加碼"
            priority_list.append({"priority": abs(diff_pct), "text": f"建議 **{dir_text}** {name} (偏離 {diff_pct:+.1f}%)"})

        analysis_data.append({
            "資產類別": name,
            "目前比例": f"{actual_pct:.1%}",
            "目標比例": f"{target_pct:.1%}",
            "偏離度": f"{diff_pct:+.1f}%",
            "狀態": status,
            "建議調整額度 (TWD)": f"{diff_twd:+,.0f}"
        })

    # 顯示優先順序
    if priority_list:
        priority_list = sorted(priority_list, key=lambda x: x['priority'], reverse=True)
        for i, item in enumerate(priority_list):
            st.warning(f"優先順序 {i+1}: {item['text']}")

    st.table(pd.DataFrame(analysis_data))

    # 6. 稅務提醒
    st.info("⚠️ 稅務提醒：美股獲利屬海外所得，年度超過 100 萬需申報；虛幣獲利依規定課稅。")

else:
    st.info("請輸入資產金額開始分析")
