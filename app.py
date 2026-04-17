<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>資產再平衡</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0d0f14;
    --surface: #161920;
    --surface2: #1e2230;
    --border: #2a2f3f;
    --accent: #4fd1c5;
    --accent2: #f6ad55;
    --danger: #fc8181;
    --success: #68d391;
    --warn: #f6e05e;
    --text: #e2e8f0;
    --muted: #718096;
    --radius: 12px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Noto Sans TC', sans-serif;
    min-height: 100vh;
    padding: 16px;
    font-size: 15px;
  }
  h1 {
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 0.05em;
    color: var(--accent);
    margin-bottom: 4px;
  }
  .subtitle { color: var(--muted); font-size: 12px; margin-bottom: 20px; }

  /* Rate bar */
  .rate-bar {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 12px 16px;
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
    flex-wrap: wrap;
  }
  .rate-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); flex-shrink: 0; }
  .rate-dot.err { background: var(--danger); }
  .rate-label { color: var(--muted); font-size: 12px; }
  .rate-val { font-family: 'DM Mono', monospace; font-size: 14px; color: var(--accent); font-weight: 500; }
  .rate-actions { margin-left: auto; display: flex; gap: 8px; }
  .btn-sm {
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text);
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
    cursor: pointer;
    font-family: inherit;
    transition: all 0.15s;
  }
  .btn-sm:hover { border-color: var(--accent); color: var(--accent); }

  /* Manual rate input */
  .manual-rate {
    display: none;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 12px 16px;
    margin-bottom: 16px;
    gap: 10px;
    align-items: center;
  }
  .manual-rate.show { display: flex; }
  .manual-rate input {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    font-family: 'DM Mono', monospace;
    font-size: 14px;
    padding: 6px 10px;
    width: 120px;
    outline: none;
  }
  .manual-rate input:focus { border-color: var(--accent); }

  /* Section */
  .section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px;
    margin-bottom: 16px;
  }
  .section-title {
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 14px;
  }

  /* Input rows */
  .input-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
  }
  .input-row:last-child { margin-bottom: 0; }
  .input-icon { font-size: 18px; flex-shrink: 0; width: 28px; text-align: center; }
  .input-meta { flex: 1; min-width: 0; }
  .input-label { font-size: 13px; color: var(--text); }
  .input-hint { font-size: 11px; color: var(--muted); }
  .input-field {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-family: 'DM Mono', monospace;
    font-size: 14px;
    padding: 8px 12px;
    width: 130px;
    text-align: right;
    outline: none;
    transition: border-color 0.15s;
    flex-shrink: 0;
  }
  .input-field:focus { border-color: var(--accent); }
  .input-currency {
    font-size: 11px;
    color: var(--muted);
    width: 36px;
    text-align: left;
    flex-shrink: 0;
  }

  /* Tolerance */
  .tolerance-row {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }
  .tolerance-item {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    min-width: 140px;
  }
  .tolerance-item label { font-size: 12px; color: var(--muted); white-space: nowrap; }
  .tolerance-item input {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    padding: 5px 8px;
    width: 60px;
    text-align: center;
    outline: none;
  }
  .tolerance-item input:focus { border-color: var(--accent); }

  /* Run button */
  .btn-run {
    width: 100%;
    background: var(--accent);
    color: #0d0f14;
    border: none;
    border-radius: var(--radius);
    font-family: 'Noto Sans TC', sans-serif;
    font-weight: 700;
    font-size: 16px;
    padding: 14px;
    cursor: pointer;
    letter-spacing: 0.05em;
    transition: opacity 0.15s, transform 0.1s;
    margin-bottom: 16px;
  }
  .btn-run:hover { opacity: 0.9; }
  .btn-run:active { transform: scale(0.98); }

  /* Results */
  #results { display: none; }
  .summary-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    flex-wrap: wrap;
    gap: 8px;
  }
  .summary-label { color: var(--muted); font-size: 12px; }
  .summary-total { font-family: 'DM Mono', monospace; font-size: 22px; font-weight: 500; color: var(--accent); }
  .summary-date { font-size: 11px; color: var(--muted); }

  /* Donut chart */
  .donut-wrap {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 16px;
    gap: 24px;
    flex-wrap: wrap;
  }
  .donut-svg { width: 150px; height: 150px; flex-shrink: 0; }
  .donut-legend { display: flex; flex-direction: column; gap: 8px; }
  .legend-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
  .legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }

  /* Asset rows */
  .asset-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 14px 16px;
    margin-bottom: 10px;
    position: relative;
    overflow: hidden;
  }
  .asset-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
  }
  .asset-card.ok::before { background: var(--success); }
  .asset-card.warn::before { background: var(--warn); }
  .asset-card.danger::before { background: var(--danger); }

  .asset-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
  .asset-name { font-size: 14px; font-weight: 500; }
  .asset-badge {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 100px;
    font-weight: 500;
  }
  .badge-ok { background: rgba(104,211,145,0.15); color: var(--success); }
  .badge-warn { background: rgba(246,224,94,0.15); color: var(--warn); }
  .badge-danger { background: rgba(252,129,129,0.15); color: var(--danger); }

  .asset-bar-wrap { background: var(--surface2); border-radius: 4px; height: 6px; margin-bottom: 8px; position: relative; }
  .asset-bar { height: 100%; border-radius: 4px; transition: width 0.6s ease; }
  .asset-bar.ok { background: var(--success); }
  .asset-bar.warn { background: var(--warn); }
  .asset-bar.danger { background: var(--danger); }
  .target-marker {
    position: absolute;
    top: -3px;
    width: 2px;
    height: 12px;
    background: var(--muted);
    border-radius: 1px;
    transform: translateX(-50%);
  }

  .asset-stats { display: flex; gap: 16px; font-size: 12px; flex-wrap: wrap; }
  .stat-item { color: var(--muted); }
  .stat-item span { color: var(--text); font-family: 'DM Mono', monospace; }

  .asset-action {
    margin-top: 10px;
    padding: 8px 12px;
    background: var(--surface2);
    border-radius: 8px;
    font-size: 13px;
    border-left: 2px solid var(--accent2);
    color: var(--accent2);
  }

  /* Priority */
  .priority-section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 14px 16px;
    margin-bottom: 16px;
  }
  .priority-title { font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); margin-bottom: 10px; }
  .priority-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 8px;
    font-size: 13px;
  }
  .priority-item:last-child { margin-bottom: 0; }
  .priority-num {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: var(--surface2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-family: 'DM Mono', monospace;
    flex-shrink: 0;
    margin-top: 1px;
  }

  /* History */
  .history-section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 14px 16px;
    margin-bottom: 16px;
  }
  .history-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .history-title { font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); }
  .history-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
    font-size: 12px;
    cursor: pointer;
    transition: color 0.15s;
  }
  .history-item:last-child { border-bottom: none; }
  .history-item:hover { color: var(--accent); }
  .history-date { color: var(--muted); }
  .history-total { font-family: 'DM Mono', monospace; }
  .history-empty { color: var(--muted); font-size: 12px; text-align: center; padding: 8px 0; }

  /* Tax note */
  .tax-note {
    background: rgba(246,173,85,0.08);
    border: 1px solid rgba(246,173,85,0.25);
    border-radius: var(--radius);
    padding: 10px 14px;
    font-size: 12px;
    color: var(--accent2);
    margin-bottom: 16px;
    line-height: 1.5;
  }

  /* Toast */
  .toast {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 100px;
    padding: 8px 18px;
    font-size: 13px;
    color: var(--text);
    opacity: 0;
    transition: opacity 0.3s;
    pointer-events: none;
    white-space: nowrap;
    z-index: 999;
  }
  .toast.show { opacity: 1; }

  /* Spinner */
  .spinner {
    display: inline-block;
    width: 12px; height: 12px;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    vertical-align: middle;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* History chart mini */
  .mini-chart { width: 100%; height: 60px; margin-top: 8px; }
</style>
</head>
<body>

<h1>📊 資產再平衡</h1>
<p class="subtitle">積極中帶保守 · 自動化分析</p>

<!-- Rate bar -->
<div class="rate-bar" id="rateBar">
  <div class="rate-dot" id="rateDot"></div>
  <span class="rate-label">美金匯率（台銀即期賣出）</span>
  <span class="rate-val" id="rateDisplay">載入中 <span class="spinner"></span></span>
  <div class="rate-actions">
    <button class="btn-sm" onclick="fetchRate()">🔄 更新</button>
    <button class="btn-sm" onclick="toggleManual()">✏️ 手動</button>
  </div>
</div>
<div class="manual-rate" id="manualRateRow">
  <span style="font-size:13px;color:var(--muted);">手動輸入匯率：</span>
  <input type="number" id="manualRate" placeholder="32.55" step="0.01">
  <button class="btn-sm" onclick="applyManual()">確認</button>
</div>

<!-- Input section -->
<div class="section">
  <div class="section-title">帳戶資產輸入</div>

  <div class="input-row">
    <div class="input-icon">🏦</div>
    <div class="input-meta">
      <div class="input-label">台幣現金</div>
      <div class="input-hint">銀行帳戶可用餘額</div>
    </div>
    <input class="input-field" id="twd_cash" type="number" placeholder="0" min="0">
    <div class="input-currency">TWD</div>
  </div>

  <div class="input-row">
    <div class="input-icon">📈</div>
    <div class="input-meta">
      <div class="input-label">台股總額</div>
      <div class="input-hint">台股證券戶市值</div>
    </div>
    <input class="input-field" id="tw_stock" type="number" placeholder="0" min="0">
    <div class="input-currency">TWD</div>
  </div>

  <div class="input-row">
    <div class="input-icon">🌐</div>
    <div class="input-meta">
      <div class="input-label">複委託</div>
      <div class="input-hint">國內券商複委託帳戶</div>
    </div>
    <input class="input-field" id="sub_broker" type="number" placeholder="0" min="0">
    <div class="input-currency">USD</div>
  </div>

  <div class="input-row">
    <div class="input-icon">🇺🇸</div>
    <div class="input-meta">
      <div class="input-label">海外美股</div>
      <div class="input-hint">Firstrade 等海外券商</div>
    </div>
    <input class="input-field" id="us_stock" type="number" placeholder="0" min="0">
    <div class="input-currency">USD</div>
  </div>

  <div class="input-row">
    <div class="input-icon">₿</div>
    <div class="input-meta">
      <div class="input-label">虛擬貨幣</div>
      <div class="input-hint">交易所加密資產</div>
    </div>
    <input class="input-field" id="crypto" type="number" placeholder="0" min="0">
    <div class="input-currency">USDT</div>
  </div>
</div>

<!-- Tolerance section -->
<div class="section">
  <div class="section-title">容忍區間設定（±%）</div>
  <div class="tolerance-row">
    <div class="tolerance-item">
      <label>美股</label>
      <input type="number" id="tol_us" value="5" min="1" max="20">
      <span style="font-size:12px;color:var(--muted);">%</span>
    </div>
    <div class="tolerance-item">
      <label>台股</label>
      <input type="number" id="tol_tw" value="5" min="1" max="20">
      <span style="font-size:12px;color:var(--muted);">%</span>
    </div>
    <div class="tolerance-item">
      <label>現金</label>
      <input type="number" id="tol_cash" value="8" min="1" max="20">
      <span style="font-size:12px;color:var(--muted);">%</span>
    </div>
    <div class="tolerance-item">
      <label>虛幣</label>
      <input type="number" id="tol_crypto" value="3" min="1" max="20">
      <span style="font-size:12px;color:var(--muted);">%</span>
    </div>
  </div>
</div>

<button class="btn-run" onclick="analyze()">🔍 開始分析</button>

<!-- Results -->
<div id="results">

  <div class="summary-card">
    <div>
      <div class="summary-label">總資產（台幣估值）</div>
      <div class="summary-total" id="totalDisplay">NT$ 0</div>
    </div>
    <div style="text-align:right;">
      <div class="summary-date" id="dateDisplay"></div>
      <div style="font-size:12px;color:var(--muted);margin-top:4px;" id="rateUsed"></div>
    </div>
  </div>

  <!-- Donut -->
  <div class="donut-wrap">
    <svg class="donut-svg" id="donutSvg" viewBox="0 0 100 100">
      <circle cx="50" cy="50" r="38" fill="none" stroke="#1e2230" stroke-width="18"/>
    </svg>
    <div class="donut-legend" id="donutLegend"></div>
  </div>

  <!-- Asset cards -->
  <div id="assetCards"></div>

  <!-- Priority -->
  <div class="priority-section" id="prioritySection" style="display:none">
    <div class="priority-title">📋 建議操作順序</div>
    <div id="priorityList"></div>
  </div>

  <!-- Tax note -->
  <div class="tax-note" id="taxNote" style="display:none">
    ⚠️ <strong>稅務提醒：</strong>美股/複委託獲利屬海外所得，年度超過 100 萬需申報最低稅負；虛幣交易獲利依財政部規定課稅，請諮詢會計師。
  </div>

  <!-- History -->
  <div class="history-section">
    <div class="history-header">
      <div class="history-title">📁 歷史紀錄</div>
      <button class="btn-sm" onclick="clearHistory()">清除</button>
    </div>
    <div id="historyList"></div>
    <svg class="mini-chart" id="miniChart"></svg>
  </div>

</div>

<div class="toast" id="toast"></div>

<script>
// ─── State ───────────────────────────────────────────────
let usdRate = null;

const TARGETS = { us: 50, tw: 25, cash: 15, crypto: 10 };
const COLORS  = { us: '#4fd1c5', tw: '#90cdf4', cash: '#68d391', crypto: '#f6ad55' };
const LABELS  = { us: '美股大類', tw: '台股', cash: '現金', crypto: '虛擬貨幣' };

// ─── Rate fetch ───────────────────────────────────────────
async function fetchRate() {
  const dot = document.getElementById('rateDot');
  const disp = document.getElementById('rateDisplay');
  disp.innerHTML = '連線中 <span class="spinner"></span>';
  dot.classList.remove('err');

  try {
    const proxy = 'https://corsproxy.io/?';
    const url = 'https://rate.bot.com.tw/xrt/flcsv/0/day';
    const res = await fetch(proxy + encodeURIComponent(url), { signal: AbortSignal.timeout(8000) });
    const text = await res.text();
    const lines = text.split('\n');
    for (const line of lines) {
      if (line.includes('USD')) {
        const cols = line.split(',');
        // col index 13 = 即期賣出
        const sell = parseFloat(cols[13]);
        if (!isNaN(sell) && sell > 20) {
          usdRate = sell;
          disp.textContent = `${sell.toFixed(2)} NTD/USD（台銀即期賣出）`;
          dot.classList.remove('err');
          showToast('📡 匯率更新成功');
          return;
        }
      }
    }
    throw new Error('parse fail');
  } catch (e) {
    dot.classList.add('err');
    disp.textContent = '抓取失敗，請手動輸入';
    showToast('⚠️ 連線失敗，請手動輸入匯率');
  }
}

function toggleManual() {
  const row = document.getElementById('manualRateRow');
  row.classList.toggle('show');
}

function applyManual() {
  const v = parseFloat(document.getElementById('manualRate').value);
  if (isNaN(v) || v < 20 || v > 50) { showToast('請輸入合理匯率（20–50）'); return; }
  usdRate = v;
  document.getElementById('rateDisplay').textContent = `${v.toFixed(2)} NTD/USD（手動輸入）`;
  document.getElementById('rateDot').classList.remove('err');
  document.getElementById('manualRateRow').classList.remove('show');
  showToast('✅ 匯率已設定');
}

// ─── Analyze ─────────────────────────────────────────────
function analyze() {
  if (!usdRate) { showToast('⚠️ 請先取得匯率'); return; }

  const twd_cash  = +document.getElementById('twd_cash').value  || 0;
  const tw_stock  = +document.getElementById('tw_stock').value  || 0;
  const sub_broker= +document.getElementById('sub_broker').value|| 0;
  const us_stock  = +document.getElementById('us_stock').value  || 0;
  const crypto    = +document.getElementById('crypto').value    || 0;

  const tol_us    = +document.getElementById('tol_us').value    || 5;
  const tol_tw    = +document.getElementById('tol_tw').value    || 5;
  const tol_cash  = +document.getElementById('tol_cash').value  || 8;
  const tol_crypto= +document.getElementById('tol_crypto').value|| 3;

  // Convert to TWD
  const usVal   = (sub_broker + us_stock) * usdRate;
  const cryptoVal = crypto * usdRate;
  const total   = twd_cash + tw_stock + usVal + cryptoVal;

  if (total === 0) { showToast('請輸入至少一個資產金額'); return; }

  const actual = {
    us:     (usVal / total * 100),
    tw:     (tw_stock / total * 100),
    cash:   (twd_cash / total * 100),
    crypto: (cryptoVal / total * 100),
  };
  const tols = { us: tol_us, tw: tol_tw, cash: tol_cash, crypto: tol_crypto };

  // Render
  document.getElementById('results').style.display = 'block';
  document.getElementById('totalDisplay').textContent = `NT$ ${fmt(total)}`;
  document.getElementById('dateDisplay').textContent  = new Date().toLocaleString('zh-TW', { month:'numeric', day:'numeric', hour:'2-digit', minute:'2-digit' });
  document.getElementById('rateUsed').textContent     = `匯率 ${usdRate.toFixed(2)}`;

  renderDonut(actual);
  renderCards(actual, tols, { usVal, tw_stock, twd_cash, cryptoVal, sub_broker, us_stock, crypto, total });
  renderPriority(actual, tols);
  saveHistory(total, actual);
  renderHistory();

  document.getElementById('taxNote').style.display = 'block';
  document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
}

// ─── Donut ────────────────────────────────────────────────
function renderDonut(actual) {
  const svg = document.getElementById('donutSvg');
  const R = 38, CX = 50, CY = 50, stroke = 18;
  const circ = 2 * Math.PI * R;
  const keys = ['us', 'tw', 'cash', 'crypto'];

  // clear previous segments
  svg.innerHTML = `<circle cx="${CX}" cy="${CY}" r="${R}" fill="none" stroke="#1e2230" stroke-width="${stroke}"/>`;

  let offset = 0;
  keys.forEach(k => {
    const pct = actual[k] / 100;
    const dash = pct * circ;
    const gap  = circ - dash;
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', CX);
    circle.setAttribute('cy', CY);
    circle.setAttribute('r', R);
    circle.setAttribute('fill', 'none');
    circle.setAttribute('stroke', COLORS[k]);
    circle.setAttribute('stroke-width', stroke);
    circle.setAttribute('stroke-dasharray', `${dash} ${gap}`);
    circle.setAttribute('stroke-dashoffset', -offset);
    circle.setAttribute('transform', `rotate(-90 ${CX} ${CY})`);
    svg.appendChild(circle);
    offset += dash;
  });

  // Legend
  const legend = document.getElementById('donutLegend');
  legend.innerHTML = keys.map(k => `
    <div class="legend-item">
      <div class="legend-dot" style="background:${COLORS[k]}"></div>
      <span style="color:var(--muted);font-size:12px;">${LABELS[k]}</span>
      <span style="font-family:'DM Mono',monospace;font-size:12px;margin-left:4px;">${actual[k].toFixed(1)}%</span>
    </div>
  `).join('');
}

// ─── Asset cards ─────────────────────────────────────────
function renderCards(actual, tols, vals) {
  const container = document.getElementById('assetCards');
  const keys = ['us', 'tw', 'cash', 'crypto'];

  container.innerHTML = keys.map(k => {
    const pct    = actual[k];
    const target = TARGETS[k];
    const tol    = tols[k];
    const diff   = pct - target;
    const absDiff= Math.abs(diff);
    const status = absDiff <= tol ? 'ok' : 'danger';
    const isDanger = status === 'danger';

    const badgeClass = isDanger ? 'badge-danger' : 'badge-ok';
    const badgeText  = isDanger ? '⚠️ 需調整' : '✅ 正常';
    const barClass   = isDanger ? 'danger' : 'ok';

    // Action
    let action = '';
    if (isDanger) {
      if (k === 'us') {
        const gapUSD = Math.abs((diff / 100) * vals.total / usdRate);
        action = diff > 0
          ? `建議賣出約 <strong>${fmt(gapUSD)} USD</strong>（複委託或海外美股減碼）`
          : `建議補足約 <strong>+${fmt(gapUSD)} USD</strong>（可分配至複委託或海外美股）`;
      } else if (k === 'tw') {
        const gapTWD = Math.abs((diff / 100) * vals.total);
        action = diff > 0
          ? `建議賣出約 <strong>NT$ ${fmt(gapTWD)}</strong> 台股`
          : `建議買入約 <strong>NT$ ${fmt(gapTWD)}</strong> 台股`;
      } else if (k === 'cash') {
        const gapTWD = Math.abs((diff / 100) * vals.total);
        action = diff > 0
          ? `現金過多，可考慮投入約 <strong>NT$ ${fmt(gapTWD)}</strong>`
          : `建議保留更多現金，約 <strong>NT$ ${fmt(gapTWD)}</strong>`;
      } else if (k === 'crypto') {
        const gapUSDT = Math.abs((diff / 100) * vals.total / usdRate);
        action = diff > 0
          ? `建議賣出約 <strong>${fmt(gapUSDT)} USDT</strong> 並轉入現金或其他資產`
          : `建議買入約 <strong>+${fmt(gapUSDT)} USDT</strong>`;
      }
    }

    // TWD value display
    let valDisplay = '';
    if (k === 'us')     valDisplay = `NT$ ${fmt(vals.usVal)}（複委託 ${fmt(vals.sub_broker)} USD ＋ 海外 ${fmt(vals.us_stock)} USD）`;
    if (k === 'tw')     valDisplay = `NT$ ${fmt(vals.tw_stock)}`;
    if (k === 'cash')   valDisplay = `NT$ ${fmt(vals.twd_cash)}`;
    if (k === 'crypto') valDisplay = `NT$ ${fmt(vals.cryptoVal)}（${fmt(vals.crypto)} USDT）`;

    const barPct = Math.min(pct, 100);
    const targetBarPct = Math.min(target, 100);

    return `
    <div class="asset-card ${status}">
      <div class="asset-header">
        <div class="asset-name">${LABELS[k]}<span style="color:var(--muted);font-size:11px;margin-left:6px;">目標 ${target}%</span></div>
        <div class="asset-badge ${badgeClass}">${badgeText}</div>
      </div>
      <div class="asset-bar-wrap">
        <div class="asset-bar ${barClass}" style="width:${barPct}%"></div>
        <div class="target-marker" style="left:${targetBarPct}%"></div>
      </div>
      <div class="asset-stats">
        <div class="stat-item">當前比例 <span>${pct.toFixed(1)}%</span></div>
        <div class="stat-item">偏離 <span style="color:${isDanger?'var(--danger)':'var(--success)'}">${diff>0?'+':''}${diff.toFixed(1)}%</span></div>
        <div class="stat-item">容忍 <span>±${tols[k]}%</span></div>
      </div>
      <div class="asset-stats" style="margin-top:6px;">
        <div class="stat-item">估值 <span>${valDisplay}</span></div>
      </div>
      ${action ? `<div class="asset-action">${action}</div>` : ''}
    </div>`;
  }).join('');
}

// ─── Priority ─────────────────────────────────────────────
function renderPriority(actual, tols) {
  const keys = ['us', 'tw', 'cash', 'crypto'];
  const alerts = keys
    .map(k => ({ k, diff: actual[k] - TARGETS[k], tol: tols[k] }))
    .filter(x => Math.abs(x.diff) > x.tol)
    .sort((a, b) => Math.abs(b.diff) - Math.abs(a.diff));

  const section = document.getElementById('prioritySection');
  const list    = document.getElementById('priorityList');

  if (alerts.length === 0) {
    section.style.display = 'none';
    return;
  }
  section.style.display = 'block';

  list.innerHTML = alerts.map((a, i) => {
    const dir = a.diff > 0 ? '減碼' : '加碼';
    const urgency = Math.abs(a.diff) > a.tol * 2 ? '🔴 優先' : '🟡 建議';
    return `<div class="priority-item">
      <div class="priority-num">${i+1}</div>
      <div>${urgency} <strong>${LABELS[a.k]}</strong> ${dir}（偏離 ${a.diff>0?'+':''}${a.diff.toFixed(1)}%）</div>
    </div>`;
  }).join('');
}

// ─── History ──────────────────────────────────────────────
function saveHistory(total, actual) {
  const history = getHistory();
  history.unshift({
    date: new Date().toLocaleString('zh-TW', { month:'numeric', day:'numeric', hour:'2-digit', minute:'2-digit' }),
    ts: Date.now(),
    total,
    actual,
    rate: usdRate,
  });
  const trimmed = history.slice(0, 20);
  try { localStorage.setItem('rebalance_history', JSON.stringify(trimmed)); } catch(e) {}
}

function getHistory() {
  try { return JSON.parse(localStorage.getItem('rebalance_history') || '[]'); } catch(e) { return []; }
}

function clearHistory() {
  try { localStorage.removeItem('rebalance_history'); } catch(e) {}
  renderHistory();
  showToast('歷史紀錄已清除');
}

function renderHistory() {
  const history = getHistory();
  const list = document.getElementById('historyList');
  if (history.length === 0) {
    list.innerHTML = '<div class="history-empty">尚無紀錄</div>';
    renderMiniChart([]);
    return;
  }
  list.innerHTML = history.slice(0, 8).map((h, i) => `
    <div class="history-item" onclick="loadHistory(${i})">
      <span class="history-date">${h.date}　匯率 ${h.rate?.toFixed(2) ?? '--'}</span>
      <span class="history-total">NT$ ${fmt(h.total)}</span>
    </div>
  `).join('');
  renderMiniChart(history.slice(0, 10).reverse());
}

function loadHistory(i) {
  const history = getHistory();
  const h = history[i];
  if (!h) return;
  showToast(`📅 ${h.date} 的快照（僅供查看）`);
}

function renderMiniChart(history) {
  const svg = document.getElementById('miniChart');
  svg.innerHTML = '';
  if (history.length < 2) return;

  const W = 320, H = 60, pad = 8;
  const totals = history.map(h => h.total);
  const min = Math.min(...totals);
  const max = Math.max(...totals);
  const range = max - min || 1;

  const pts = totals.map((t, i) => {
    const x = pad + (i / (totals.length - 1)) * (W - pad*2);
    const y = H - pad - ((t - min) / range) * (H - pad*2);
    return `${x},${y}`;
  });

  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.innerHTML = `
    <polyline points="${pts.join(' ')}" fill="none" stroke="var(--accent)" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>
    ${totals.map((t,i) => {
      const [x, y] = pts[i].split(',');
      return `<circle cx="${x}" cy="${y}" r="3" fill="var(--accent)"/>`;
    }).join('')}
  `;
}

// ─── Utils ────────────────────────────────────────────────
function fmt(n) {
  return Math.round(n).toLocaleString('zh-TW');
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}

// ─── Init ─────────────────────────────────────────────────
fetchRate();
renderHistory();
</script>
</body>
</html>
