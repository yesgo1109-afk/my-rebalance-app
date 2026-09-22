import streamlit as st
import requests
import pandas as pd
import io
from datetime import datetime

# ── 頁面設定 ────────────────────────────────────────────────
st.set_page_config(page_title="資產再平衡系統", page_icon="📊", layout="centered")

# ── 自定義 CSS ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }
.metric-card { background: #1e2230; border-radius: 12px; padding: 16px 20px; border-left: 4px solid #4fd1c5; }
.action-box {
    background: rgba(246,173,85,0.1);
    border-left: 3px solid #f6ad55;
    border-radius: 6px;
    padding: 8px 12px;
    margin-top: 8px;
    font-size: 14px;
}
.debt-box {
    background: rgba(252,129,129,0.08);
    border-left: 3px solid #fc8181;
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# ── 設定 ────────────────────────────────────────────────────
TARGETS = {"美股大類": 45, "台股": 40, "現金": 5, "虛擬貨幣": 10}
COLORS  = ["#4fd1c5", "#90cdf4", "#68d391", "#f6ad55"]

# ── Supabase 工具函式 ────────────────────────────────────────
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

def sb_load_history():
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/asset_history",
            headers=HEADERS,
            params={"order": "date.desc", "limit": "30"},
            timeout=8,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.warning(f"讀取歷史失敗：{e}")
    return []

def sb_save_history(row: dict):
    try:
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/asset_history",
            headers=HEADERS,
            json=row,
            timeout=8,
        )
        return r.status_code in (200, 201)
    except Exception as e:
        st.warning(f"儲存失敗：{e}")
        return False

def sb_clear_history():
    try:
        r = requests.delete(
            f"{SUPABASE_URL}/rest/v1/asset_history",
            headers={**HEADERS, "Prefer": "return=minimal"},
            params={"date": "neq.null"},
            timeout=8,
        )
        return r.status_code in (200, 204)
    except Exception as e:
        st.warning(f"清除失敗：{e}")
        return False

# ── 匯率抓取 ────────────────────────────────────────────────
@st.cache_data(ttl=1800)
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

# ── 標題 ────────────────────────────────────────────────────
st.title("📊 資產再平衡指揮中心")
st.caption("積極中帶保守 · 自動化分析")

# ── 匯率區塊 ────────────────────────────────────────────────
st.subheader("💱 美金匯率（台銀即期賣出）")
col_rate, col_btn = st.columns([3, 1])
with col_btn:
    if st.button("🔄 更新"):
        st.cache_data.clear()

auto_rate, err = fetch_usd_rate()
if auto_rate:
    col_rate.success(f"📡 台銀即期賣出：**{auto_rate:.2f} NTD/USD**")
    default_rate = auto_rate
else:
    col_rate.warning(f"⚠️ 自動抓取失敗（{err}）")
    default_rate = 31.5

if st.checkbox("✏️ 手動輸入匯率"):
    usd_rate = st.number_input("輸入匯率", min_value=20.0, max_value=50.0,
                               value=default_rate, step=0.01, format="%.2f")
else:
    usd_rate = auto_rate if auto_rate else default_rate

st.divider()

# ── 帳戶輸入 ────────────────────────────────────────────────
st.subheader("🏦 帳戶資產輸入")
col1, col2 = st.columns(2)
with col1:
    twd_cash   = st.number_input("🏦 台幣現金 (TWD)",          min_value=0, value=0, step=10000, help="銀行帳戶可用餘額")
    tw_stock   = st.number_input("📈 台股總額 (TWD)",          min_value=0, value=0, step=10000, help="台股證券戶市值")
    sub_broker = st.number_input("🌐 複委託 (USD)",            min_value=0, value=0, step=100,   help="國內券商複委託帳戶")
with col2:
    us_stock   = st.number_input("🇺🇸 海外美股 (USD)",        min_value=0, value=0, step=100,   help="Firstrade 等海外券商")
    crypto_usd = st.number_input("₿ 虛擬貨幣 (USDT)",         min_value=0, value=0, step=100,   help="交易所加密資產")
    crypto_twd = st.number_input("₿ 虛擬貨幣-台幣帳戶 (TWD)", min_value=0, value=0, step=1000,  help="台幣計價的加密資產")

st.divider()

# ── 貸款輸入 ────────────────────────────────────────────────
st.subheader("🏧 貸款餘額輸入")
st.caption("輸入目前尚未還清的貸款金額，用於計算淨資產")

loan_count = st.number_input("貸款筆數", min_value=1, max_value=5, value=1, step=1)
loans = []
loan_cols = st.columns(2)
for i in range(loan_count):
    with loan_cols[i % 2]:
        name = st.text_input(f"貸款名稱 {i+1}", value=f"貸款{i+1}", key=f"loan_name_{i}")
        amount = st.number_input(f"餘額 (TWD) {i+1}", min_value=0, value=0, step=10000, key=f"loan_amt_{i}")
        loans.append({"name": name, "amount": amount})

total_loan = sum(l["amount"] for l in loans)

st.divider()

# ── 容忍區間 ────────────────────────────────────────────────
st.subheader("⚙️ 容忍區間設定（±%）")
c1, c2, c3, c4 = st.columns(4)
tol_us     = c1.number_input("美股", 1, 20, 5,  key="tol_us")
tol_tw     = c2.number_input("台股", 1, 20, 5,  key="tol_tw")
tol_cash   = c3.number_input("現金", 1, 20, 8,  key="tol_cash")
tol_crypto = c4.number_input("虛幣", 1, 20, 3,  key="tol_crypto")
tols = {"美股大類": tol_us, "台股": tol_tw, "現金": tol_cash, "虛擬貨幣": tol_crypto}

st.divider()

# ── 分析 ────────────────────────────────────────────────────
if st.button("🔍 開始分析並儲存紀錄", type="primary", use_container_width=True):

    us_twd           = (sub_broker + us_stock) * usd_rate
    crypto_total_twd = (crypto_usd * usd_rate) + crypto_twd
    total_asset      = twd_cash + tw_stock + us_twd + crypto_total_twd
    net_asset        = total_asset - total_loan   # 淨資產 = 總資產 - 貸款

    if total_asset == 0:
        st.error("請輸入至少一個資產金額")
        st.stop()
    if net_asset <= 0:
        st.error("⚠️ 貸款餘額超過總資產，無法進行再平衡計算")
        st.stop()

    # 用淨資產計算比例
    actual = {
        "美股大類": us_twd           / net_asset * 100,
        "台股":     tw_stock         / net_asset * 100,
        "現金":     twd_cash         / net_asset * 100,
        "虛擬貨幣": crypto_total_twd / net_asset * 100,
    }

    # ── 總覽 ──
    st.subheader("📋 分析結果")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("總資產（台幣估值）", f"NT$ {total_asset:,.0f}")
    col_b.metric("貸款總餘額", f"NT$ {total_loan:,.0f}", delta=f"-{total_loan:,.0f}", delta_color="inverse")
    col_c.metric("淨資產", f"NT$ {net_asset:,.0f}")

    # 貸款明細
    if total_loan > 0:
        st.markdown("**貸款明細：**")
        for l in loans:
            if l["amount"] > 0:
                pct_of_asset = l["amount"] / total_asset * 100
                st.markdown(
                    f'<div class="debt-box">🏧 <b>{l["name"]}</b>　NT$ {l["amount"]:,.0f}　<span style="color:#fc8181;">佔總資產 {pct_of_asset:.1f}%</span></div>',
                    unsafe_allow_html=True
                )

    st.caption(f"分析時間：{now_str[5:]}　匯率：{usd_rate:.2f}")

    # ── 比例圖（基於淨資產）──
    st.subheader("📊 資產比例圖（以淨資產為基準）")
    chart_data = pd.DataFrame({"類別": list(actual.keys()), "比例": list(actual.values())})
    st.bar_chart(chart_data.set_index("類別"), color="#4fd1c5", horizontal=True)

    # ── 各類別分析 ──
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
            p1.metric("當前比例", f"{pct:.1f}%")
            p2.metric("目標比例", f"{target}%")
            p3.metric("偏離幅度", diff_str, delta_color="inverse" if diff > 0 else "normal")

            if cat == "美股大類":
                st.caption(f"NT$ {us_twd:,.0f}（複委託 {sub_broker:,} USD ＋ 海外 {us_stock:,} USD）")
            elif cat == "台股":
                st.caption(f"NT$ {tw_stock:,.0f}")
            elif cat == "現金":
                st.caption(f"NT$ {twd_cash:,.0f}")
            elif cat == "虛擬貨幣":
                st.caption(f"NT$ {crypto_total_twd:,.0f}（{crypto_usd:,} USDT ＋ NT$ {crypto_twd:,}）")

            st.progress(min(pct / 100, 1.0), text=f"目標線：{target}%")

            if not is_ok:
                alerts.append((cat, diff, tol))
                gap_twd = abs(diff / 100 * net_asset)   # 以淨資產計算缺口
                gap_usd = gap_twd / usd_rate
                if cat == "美股大類":
                    action = f"建議{'賣出' if diff>0 else '補足'} **{gap_usd:,.0f} USD**"
                elif cat == "台股":
                    action = f"建議{'賣出' if diff>0 else '買入'} **NT$ {gap_twd:,.0f}** 台股"
                elif cat == "現金":
                    action = f"現金{'過多，可考慮投入' if diff>0 else '不足，建議保留'} **NT$ {gap_twd:,.0f}**"
                elif cat == "虛擬貨幣":
                    action = f"建議{'賣出' if diff>0 else '買入'} **{gap_usd:,.0f} USDT**"
                st.markdown(f'<div class="action-box">💡 {action}</div>', unsafe_allow_html=True)

    # ── 操作順序 ──
    if alerts:
        st.subheader("📋 建議操作順序")
        for i, (cat, diff, tol) in enumerate(sorted(alerts, key=lambda x: abs(x[1]), reverse=True), 1):
            dir_str = "減碼" if diff > 0 else "加碼"
            urgency = "🔴 優先" if abs(diff) > tol * 2 else "🟡 建議"
            st.markdown(f"**{i}.** {urgency} **{cat}** {dir_str}（偏離 {diff:+.1f}%）")
        st.info("⚠️ **稅務提醒：** 美股/複委託獲利屬海外所得，年度超過 100 萬需申報最低稅負；虛幣交易獲利依財政部規定課稅，請諮詢會計師。")

    # ── 儲存至 Supabase ──
    row = {
        "date":         now_str,
        "total":        round(total_asset, 0),
        "net_asset":    round(net_asset, 0),
        "total_loan":   round(total_loan, 0),
        "usd_rate":     round(usd_rate, 2),
        "us_stock_pct": round(actual["美股大類"], 2),
        "tw_stock_pct": round(actual["台股"], 2),
        "cash_pct":     round(actual["現金"], 2),
        "crypto_pct":   round(actual["虛擬貨幣"], 2),
    }
    if sb_save_history(row):
        st.success("✅ 分析完成，紀錄已永久儲存至雲端！")
    else:
        st.warning("⚠️ 分析完成，但雲端儲存失敗，請檢查 Secrets 設定。")

# ── 歷史紀錄 ────────────────────────────────────────────────
st.divider()
st.subheader("📁 歷史趨勢紀錄")

history = sb_load_history()
if history:
    df = pd.DataFrame(history)

    # 相容舊資料（沒有 net_asset / total_loan 欄位）
    for col in ["net_asset", "total_loan"]:
        if col not in df.columns:
            df[col] = None

    display_cols = ["date", "total", "net_asset", "total_loan", "usd_rate",
                    "us_stock_pct", "tw_stock_pct", "cash_pct", "crypto_pct"]
    display_df = df[display_cols].copy()
    display_df.columns = ["時間", "總資產(NT$)", "淨資產(NT$)", "貸款(NT$)",
                          "匯率", "美股%", "台股%", "現金%", "虛幣%"]
    st.dataframe(display_df.head(15), use_container_width=True, hide_index=True)

    if len(df) > 1:
        chart_df = df[["date", "total", "net_asset"]].copy()
        chart_df = chart_df.dropna(subset=["date"])
        chart_df["date"] = pd.to_datetime(chart_df["date"])
        chart_df = chart_df.set_index("date").sort_index()
        chart_df.columns = ["總資產", "淨資產"]
        st.line_chart(chart_df, color=["#4fd1c5", "#fc8181"])

    csv = display_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 下載完整 CSV 備份", data=csv, file_name="asset_history.csv", mime="text/csv")

    if st.button("🗑️ 清除所有歷史紀錄"):
        if sb_clear_history():
            st.success("已清除！")
            st.rerun()
else:
    st.caption("尚無紀錄，完成第一次分析後會自動儲存至 Supabase。")
