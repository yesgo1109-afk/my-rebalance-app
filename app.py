import streamlit as st
import pandas as pd
import requests
import io
import csv

st.set_page_config(page_title="資產再平衡", page_icon="📊")
st.title("📊 資產再平衡指揮中心")

# 抓取台銀匯率
@st.cache_data(ttl=3600)
def get_rate():
    try:
        r = requests.get("https://rate.bot.com.tw/xrt/flcsv/0/day")
        f = io.StringIO(r.text)
        reader = csv.reader(f)
        for row in reader:
            if 'USD' in row[0]: return float(row[13])
        return 32.5
    except: return 32.5

usd_rate = get_rate()
st.sidebar.write(f"今日美金匯率: {usd_rate}")

# 輸入區
c1, c2 = st.columns(2)
with c1:
    twd_cash = st.number_input("台幣現金 (TWD)", value=0)
    tw_stock = st.number_input("台股總額 (TWD)", value=0)
    crypto = st.number_input("虛擬貨幣 (USDT)", value=0)
with c2:
    sub_broker = st.number_input("複委託 (USD)", value=0)
    us_stock = st.number_input("海外美股 (USD)", value=0)

# 計算邏輯
us_twd = (sub_broker + us_stock) * usd_rate
crypto_twd = crypto * usd_rate
total = twd_cash + tw_stock + us_twd + crypto_twd

if total > 0:
    st.divider()
    st.subheader(f"總資產估值：NT$ {total:,.0f}")
    
    # 比例分析
    targets = {"美股類別": 0.50, "台股": 0.25, "現金": 0.15, "虛擬貨幣": 0.10}
    actuals = {"美股類別": us_twd, "台股": tw_stock, "現金": twd_cash, "虛擬貨幣": crypto_twd}
    
    res = []
    for name, target in targets.items():
        curr_pct = actuals[name] / total
        diff = (total * target) - actuals[name]
        res.append({"類別": name, "目前比例": f"{curr_pct:.1%}", "目標": f"{target:.1%}", "建議調整": f"{diff:,.0f}"})
    
    st.table(pd.DataFrame(res))
