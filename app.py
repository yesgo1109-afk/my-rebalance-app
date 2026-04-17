import streamlit as st
import requests
import pandas as pd
import io
from datetime import datetime
import json

# ── Page config ────────────────────────────────────────────
st.set_page_config(
    page_title="資產再平衡",
    page_icon="📊",
    layout="centered",
)

# ── Custom CSS ─────────────────────────────────────────────
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
.ok-card    { border-left-color: #68d391; }
.warn-card  { border-left-color: #fc8181; }
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

# ── Constants ──────────────────────────────────────────────
TARGETS = {"美股大類": 50, "台股": 25, "現金": 15, "虛擬貨幣": 10}
COLORS  = ["#4fd1c5", "#90cdf4", "#68d391", "#f6ad55"]

# ── Session state: history ─────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []

# ── Rate fetch ─────────────────────────────────────────────
@st.cache_data(ttl=1800)  # cache 30 min
def fetch_usd_rate():
    try:
        proxy = "https://corsproxy.io/?"
        url   = "https://rate.bot.com.tw/xrt/flcsv/0/day"
        r = requests.get(proxy + url, timeout=8)
        r.encoding = "utf-8"
        df = pd.read_csv(io.StringIO(r.text), header=None)
        row = df[df[0].astype(str).str.contains("USD", na=False)]
        if not row.empty:
            sell = float(row.iloc[0, 13])
            if 20 < sell < 60:
                return sell, None
    except Exception as e:
        return None, str(e)
    return None, "找不到 USD 欄位"

# ── Header ─────────────────────────────────────────────────
st.title("📊 資產再平衡")
st.caption("積極中帶保守 · 自動化分析")

# ── Rate section ───────────────────────────────────────────
st.subheader("💱 美金匯率（台銀即期賣出）")

col_rate, col_btn = st.columns([3, 1])
with col_rate:
    rate_placeholder = st.empty()
with col_btn:
    refresh = st.button("🔄 更新匯率")

if refresh:
    st.cache_data.clear()

auto_rate, err = fetch_usd_rate()

if auto_rate:
    rate_placeholder.success(f"📡 台銀即期賣出：**{auto_rate:.2f} NTD/USD**")
    default_rate = auto_rate
else:
    rate_placeholder.warning(f"⚠️ 自動抓取失敗（{err}），請手動輸入")
    default_rate = 32.5

manual_toggle = st.checkbox("✏️ 手動輸入匯率")
if manual_toggle:
    usd_rate = st.number_input("輸入匯率", min_value=20.0, max_value=50.0,
                               value=default_rate, step=0.01, format="%.2f")
else:
    usd_rate = auto_rate if auto_rate else default_rate

st.divider()

# ── Input section ──────────────────────────────────────────
st.subheader("🏦 帳戶資產輸入")

col1, col2 = st.columns(2)
with col1:
    twd_cash   = st.number_input("🏦 台幣現金 (TWD)", min_value=0, value=0, step=10000, help="銀行帳戶可用餘額")
    tw_stock   = st.number_input("📈 台股總額 (TWD)", min_value=0, value=0, step=10000, help="台股證券戶市值")
    sub_broker = st.number_input("🌐 複委託 (USD)",   min_value=0, value=0, step=100,   help="國內券商複委託帳戶")
with col2:
    us_stock   = st.number_input("🇺🇸 海外美股 (USD)", min_value=0, value=0, step=100,  help="Firstrade 等海外券商")
    crypto     = st.number_input("₿ 虛擬貨幣 (USDT)", min_value=0, value=0, step=100,  help="交易所加密資產")

st.divider()

# ── Tolerance section ──────────────────────────────────────
st.subheader("⚙️ 容忍區間設定（±%）")

c1, c2, c3, c4 = st.columns(4)
tol_us     = c1.number_input("美股",     1, 20, 5,  key="tol_us")
tol_tw     = c2.number_input("台股",     1, 20, 5,  key="tol_tw")
tol_cash   = c3.number_input("現金",     1, 20, 8,  key="tol_cash")
tol_crypto = c4.number_input("虛幣",     1, 20, 3,  key="tol_crypto")

tols = {"美股大類": tol_us, "台股": tol_tw, "現金": tol_cash, "虛擬貨幣": tol_crypto}

st.divider()

# ── Analyze ────────────────────────────────────────────────
if st.button("🔍 開始分析", type="primary", use_container_width=True):

    us_twd     = (sub_broker + us_stock) * usd_rate
    crypto_twd = crypto * usd_rate
    total      = twd_cash + tw_stock + us_twd + crypto_twd

    if total == 0:
        st.error("請輸入至少一個資產金額")
        st.stop()

    actual = {
        "美股大類":  us_twd     / total * 100,
        "台股":      tw_stock   / total * 100,
        "現金":      twd_cash   / total * 100,
        "虛擬貨幣":  crypto_twd / total * 100,
    }

    # ── Summary ──
    st.subheader("📋 分析結果")
    now_str = datetime.now().strftime("%m/%d %H:%M")
    col_total, col_date = st.columns(2)
    col_total.metric("總資產（台幣估值）", f"NT$ {total:,.0f}")
    col_date.metric("分析時間", now_str)

    # ── Donut chart ──
    chart_data = pd.DataFrame({
        "類別": list(actual.keys()),
        "比例": list(actual.values()),
    })
    st.subheader("📊 資產比例圖")
    st.bar_chart(chart_data.set_index("類別"), color=COLORS, horizontal=True)

    # ── Asset cards ──
    st.subheader("📈 各類別分析")

    alerts = []
    for cat in ["美股大類", "台股", "現金", "虛擬貨幣"]:
        pct    = actual[cat]
        target = TARGETS[cat]
        tol    = tols[cat]
        diff   = pct - target
        is_ok  = abs(diff) <= tol

        status_icon = "✅" if is_ok else "⚠️"
        diff_str    = f"+{diff:.1f}%" if diff > 0 else f"{diff:.1f}%"

        with st.expander(f"{status_icon} **{cat}**　{pct:.1f}% / 目標 {target}%　偏離 {diff_str}", expanded=not is_ok):
            p1, p2, p3 = st.columns(3)
            p1.metric("當前比例",  f"{pct:.1f}%")
            p2.metric("目標比例",  f"{target}%")
            p3.metric("偏離幅度",  diff_str, delta_color="inverse" if diff > 0 else "normal")

            # Value breakdown
            if cat == "美股大類":
                st.caption(f"NT$ {us_twd:,.0f}（複委託 {sub_broker:,} USD ＋ 海外 {us_stock:,} USD）")
            elif cat == "台股":
                st.caption(f"NT$ {tw_stock:,.0f}")
            elif cat == "現金":
                st.caption(f"NT$ {twd_cash:,.0f}")
            elif cat == "虛擬貨幣":
                st.caption(f"NT$ {crypto_twd:,.0f}（{crypto:,} USDT）")

            # Progress bar
            st.progress(min(pct / 100, 1.0), text=f"目標線：{target}%")

            # Action
            if not is_ok:
                alerts.append((cat, diff, tol))
                gap_twd = abs(diff / 100 * total)
                gap_usd = gap_twd / usd_rate

                if cat == "美股大類":
                    action = f"建議{'賣出' if diff>0 else '補足'} **{gap_usd:,.0f} USD**"
                elif cat == "台股":
                    action = f"建議{'賣出' if diff>0 else '買入'} **NT$ {gap_twd:,.0f}** 台股"
                elif cat == "現金":
                    action = f"現金{'過多，可考慮投入' if diff>0 else '不足，建議保留'} **NT$ {gap_twd:,.0f}**"
                elif cat == "虛擬貨幣":
                    action = f"建議{'賣出' if diff>0 else '買入'} **{gap_usd:,.0f} USDT**"

                st.markdown(f"""
                <div class="action-box">
                    💡 {action}
                </div>
                """, unsafe_allow_html=True)

    # ── Priority ──
    if alerts:
        st.subheader("📋 建議操作順序")
        alerts_sorted = sorted(alerts, key=lambda x: abs(x[1]), reverse=True)
        for i, (cat, diff, tol) in enumerate(alerts_sorted, 1):
            dir_str = "減碼" if diff > 0 else "加碼"
            urgency = "🔴 優先" if abs(diff) > tol * 2 else "🟡 建議"
            st.markdown(f"**{i}.** {urgency} **{cat}** {dir_str}（偏離 {diff:+.1f}%）")

    # ── Tax note ──
    if alerts:
        st.info("⚠️ **稅務提醒：** 美股/複委託獲利屬海外所得，年度超過 100 萬需申報最低稅負；虛幣交易獲利依財政部規定課稅，請諮詢會計師。")

    # ── Save history ──
    st.session_state.history.insert(0, {
        "date":   now_str,
        "total":  total,
        "rate":   usd_rate,
        "actual": actual,
    })
    st.session_state.history = st.session_state.history[:20]

# ── History ────────────────────────────────────────────────
st.divider()
st.subheader("📁 歷史紀錄")

if st.session_state.history:
    hist_df = pd.DataFrame([
        {"時間": h["date"], "總資產 (NT$)": f"{h['total']:,.0f}", "匯率": f"{h['rate']:.2f}"}
        for h in st.session_state.history
    ])
    st.dataframe(hist_df, use_container_width=True, hide_index=True)

    # Mini trend chart
    totals = [h["total"] for h in reversed(st.session_state.history)]
    if len(totals) > 1:
        trend_df = pd.DataFrame({"總資產": totals})
        st.line_chart(trend_df, color=["#4fd1c5"])

    if st.button("🗑️ 清除歷史紀錄"):
        st.session_state.history = []
        st.rerun()
else:
    st.caption("尚無紀錄，完成第一次分析後會自動儲存。")
