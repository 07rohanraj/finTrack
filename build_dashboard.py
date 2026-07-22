"""
Generate an interactive HTML dashboard for spending analysis.
Run: python build_dashboard.py
Output: spending_dashboard.html (open in browser)
"""
import pandas as pd
import json
from pathlib import Path

df = pd.read_excel('TransactionStatement.xlsx')
df['Datetime'] = pd.to_datetime(df['Date'], format='%b %d, %Y')
df['HourOfDay'] = pd.to_datetime(df['Time'], format='%I:%M %p').dt.hour
df['IsWeekend'] = df['Datetime'].dt.dayofweek >= 5
df['DayName'] = df['Datetime'].dt.day_name()
df['MonthStr'] = df['Datetime'].dt.strftime('%Y-%m')
df['DateStr'] = df['Datetime'].dt.strftime('%Y-%m-%d')
df['QuarterStr'] = df['Datetime'].dt.to_period('Q').astype(str)

EXCLUDE = {'Personal Transfers', 'Investment', 'Bank Transfer'}

def categorize(payee):
    p = payee.lower()
    if any(k in p for k in ['upstox', 'icici prudential', 'zerodha', 'groww']): return 'Investment'
    if any(k in p for k in ['bmtc', 'bmrc', 'metro rail', 'bangalore metro', 'petrol', 'diesel', 'yash anand fuel', 'krishna petroleum', 'dharamaa service']): return 'Transport & Fuel'
    if any(k in p for k in ['jio', 'airtel', 'prepaid recharg']): return 'Mobile Recharge'
    if any(k in p for k in ['myntra', 'flipkart', 'amazon', 'meesho', 'zepto', 'zudio', 'ajio', 'nykaa', 'tata cliq', 'ekart', 'anuyojya', 'city enterprises', 'garment']): return 'Shopping & E-Commerce'
    if any(k in p for k in ['google play', 'google india digital', 'youtube', 'netflix', 'hotstar', 'spotify', 'kukufm', 'testbook', 'bookmyshow', 'razorpay']): return 'Subscriptions & Digital'
    if any(k in p for k in ['shaadi ki biryani', 'shaad ki', 'biryani', 'hotel', 'restaurant', 'cafe', 'coffee', 'pizza', 'bakery', 'food', 'juice', 'tea', 'momos', 'morning star', 'hungry heist', 'pappu nishad', 'richmond soft', 'soft drink', 'krishna food', 'sivam bengali', 'j and b kitchen', 'green theory', 'varaha cafe', 'tea break', 'chirus', 'ponlait', 'milon juice', 'divya juice', 'juice bar', 'fruit shope', 'bharathi fast', 'y v tea', 'quick pick coffee', 'kannamma fruit', 'amman fruit', 'sbm store', 'city store', 'sri ganga', 'sri vinayaka', 'sri brahmalingeswara', 'bhrama lingeshwara', 'sri neevi', 'y v tea shop']): return 'Food & Dining'
    if any(k in p for k in ['mangalore fresh', 'manglore fresh', 'sagaya raj', 'nandhini', 'star bazaar', 'supermarket', 'royal mart', 'vegetable', 'fruit', 'coconut', 'condiment', 'groceries', 'amazon pay groceries', 'pan shop', 'olive mart', 'chaithra', 'kamakshi', 'doddamma', 'sri durga', 'mother dairy', 'sri lakshmi', 'sri brahmalingeswara juice', 'y v tea stall', 'kamakshi vegetable']): return 'Groceries & Essentials'
    if any(k in p for k in ['medplus', 'medical', 'pharmacy', 'fatima', 'mamtha', 'sachin medical', 'sanjay medical']): return 'Medical & Health'
    if any(k in p for k in ['irctc', 'indian railways', 'train', 'flight', 'amazon flights', 'redbus', 'paytm travel', 'palm suites']): return 'Travel & Stays'
    if any(k in p for k in ['bank account']): return 'Bank Transfer'
    if any(k in p for k in ['bill paid', 'credit card']): return 'Credit Card Payment'
    if any(k in p for k in ['mithila time', 'optical', 'watch', 'salon', 'saloon', 'gents parlour', 'barber']): return 'Personal Care'
    if any(k in p for k in ['electricity', 'water bill', 'gas bill', 'broadband', 'wifi']): return 'Utilities'
    return 'Personal Transfers'

debits_all = df[df['Type'] == 'Debit'].copy()
debits_all['Category'] = debits_all['Transaction Details'].apply(categorize)
debits = debits_all[~debits_all['Category'].isin(EXCLUDE)].copy()
debits['CleanName'] = debits['Transaction Details'].str.replace(r'^Paid to ', '', regex=True).str.replace(r'^Paid ', '', regex=True)

# Build JSON data for the dashboard
records = []
for _, row in debits.iterrows():
    records.append({
        'date': row['DateStr'],
        'month': row['MonthStr'],
        'quarter': row['QuarterStr'],
        'time': row['Time'],
        'hour': int(row['HourOfDay']),
        'day': row['DayName'],
        'name': row['CleanName'],
        'amount': float(row['Amount']),
        'category': row['Category'],
        'txnId': row['Transaction ID'],
        'utr': row['UTR No'],
        'weekend': bool(row['IsWeekend'])
    })

data_json = json.dumps(records)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Spending Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root {{
    --bg: #0f1117;
    --card: #1a1d29;
    --border: #2a2d3a;
    --text: #e4e6eb;
    --muted: #8b8fa3;
    --accent: #6c5ce7;
    --green: #00b894;
    --red: #e17055;
    --orange: #fdcb6e;
    --blue: #74b9ff;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg); color: var(--text);
    padding: 16px; min-height: 100vh;
  }}
  h1 {{
    text-align: center; font-size: 1.6em; margin-bottom: 4px;
    background: linear-gradient(135deg, #6c5ce7, #74b9ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }}
  .subtitle {{ text-align: center; color: var(--muted); font-size: 0.9em; margin-bottom: 20px; }}

  /* Filters */
  .filters {{
    display: flex; gap: 12px; flex-wrap: wrap; justify-content: center;
    margin-bottom: 20px; padding: 14px; background: var(--card);
    border-radius: 12px; border: 1px solid var(--border);
  }}
  .filters label {{ color: var(--muted); font-size: 0.82em; display: block; margin-bottom: 4px; }}
  .filters select, .filters input {{
    background: var(--bg); color: var(--text); border: 1px solid var(--border);
    border-radius: 8px; padding: 8px 12px; font-size: 0.88em; outline: none;
  }}
  .filters select:focus, .filters input:focus {{ border-color: var(--accent); }}
  .filter-group {{ display: flex; flex-direction: column; }}
  .btn-reset {{
    background: var(--accent); color: white; border: none; border-radius: 8px;
    padding: 8px 20px; cursor: pointer; font-size: 0.88em; align-self: flex-end;
  }}
  .btn-reset:hover {{ opacity: 0.85; }}

  /* Stats row */
  .stats {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px; margin-bottom: 20px;
  }}
  .stat-card {{
    background: var(--card); border: 1px solid var(--border); border-radius: 12px;
    padding: 16px; text-align: center;
  }}
  .stat-card .label {{ color: var(--muted); font-size: 0.78em; text-transform: uppercase; letter-spacing: 0.5px; }}
  .stat-card .value {{ font-size: 1.5em; font-weight: 700; margin-top: 4px; }}
  .stat-card .sub {{ color: var(--muted); font-size: 0.78em; margin-top: 2px; }}

  /* Charts grid */
  .charts {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;
  }}
  .chart-box {{
    background: var(--card); border: 1px solid var(--border); border-radius: 12px;
    padding: 12px; min-height: 380px;
  }}
  .chart-box.full {{ grid-column: 1 / -1; }}
  .chart-title {{
    font-size: 0.95em; font-weight: 600; padding: 6px 8px 4px;
    border-bottom: 1px solid var(--border); margin-bottom: 8px;
  }}

  /* Table */
  .table-wrap {{
    background: var(--card); border: 1px solid var(--border); border-radius: 12px;
    padding: 16px; overflow-x: auto;
  }}
  .table-header {{
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 12px; flex-wrap: wrap; gap: 8px;
  }}
  .table-header h3 {{ font-size: 1.05em; }}
  .search-box {{
    background: var(--bg); color: var(--text); border: 1px solid var(--border);
    border-radius: 8px; padding: 8px 12px; font-size: 0.85em; width: 260px; outline: none;
  }}
  .search-box:focus {{ border-color: var(--accent); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.82em; }}
  th {{
    text-align: left; padding: 10px 8px; border-bottom: 2px solid var(--border);
    color: var(--muted); cursor: pointer; user-select: none; white-space: nowrap;
  }}
  th:hover {{ color: var(--accent); }}
  th .sort-arrow {{ font-size: 0.75em; margin-left: 3px; }}
  td {{ padding: 9px 8px; border-bottom: 1px solid var(--border); }}
  tr:hover td {{ background: rgba(108, 92, 231, 0.08); }}
  .cat-badge {{
    display: inline-block; padding: 2px 8px; border-radius: 10px;
    font-size: 0.85em; font-weight: 500; white-space: nowrap;
  }}
  .row-count {{ color: var(--muted); font-size: 0.82em; margin-top: 10px; }}
  .amount-cell {{ font-weight: 600; text-align: right; }}

  @media (max-width: 900px) {{
    .charts {{ grid-template-columns: 1fr; }}
    .chart-box.full {{ grid-column: 1; }}
  }}
</style>
</head>
<body>

<h1>Spending Dashboard</h1>
<p class="subtitle">PhonePe Statement &mdash; Jun 2024 to Jul 2026 &mdash; Account XX6650 &mdash; Actual Spending (excl. Transfers &amp; Investments)</p>

<!-- Filters -->
<div class="filters" id="filters">
  <div class="filter-group">
    <label>Category</label>
    <select id="fCategory"><option value="all">All Categories</option></select>
  </div>
  <div class="filter-group">
    <label>From</label>
    <input type="month" id="fFrom" />
  </div>
  <div class="filter-group">
    <label>To</label>
    <input type="month" id="fTo" />
  </div>
  <div class="filter-group">
    <label>Day Type</label>
    <select id="fDayType">
      <option value="all">All Days</option>
      <option value="weekday">Weekdays</option>
      <option value="weekend">Weekends</option>
    </select>
  </div>
  <button class="btn-reset" onclick="resetFilters()">Reset</button>
</div>

<!-- Stats -->
<div class="stats" id="statsRow"></div>

<!-- Charts -->
<div class="charts">
  <div class="chart-box" id="catPieBox">
    <div class="chart-title">Spending by Category (click to drill)</div>
    <div id="catPie" style="width:100%;height:350px;"></div>
  </div>
  <div class="chart-box" id="catBarBox">
    <div class="chart-title">Category Comparison</div>
    <div id="catBar" style="width:100%;height:350px;"></div>
  </div>
  <div class="chart-box full">
    <div class="chart-title">Monthly Spending Trend</div>
    <div id="monthly" style="width:100%;height:320px;"></div>
  </div>
  <div class="chart-box">
    <div class="chart-title">Top 15 Payees</div>
    <div id="topPayees" style="width:100%;height:380px;"></div>
  </div>
  <div class="chart-box">
    <div class="chart-title">Spending by Hour of Day</div>
    <div id="hourly" style="width:100%;height:380px;"></div>
  </div>
  <div class="chart-box full">
    <div class="chart-title">Daily Spending (click & drag to zoom, double-click to reset)</div>
    <div id="dailyScatter" style="width:100%;height:300px;"></div>
  </div>
  <div class="chart-box">
    <div class="chart-title">Weekday vs Weekend</div>
    <div id="weekendChart" style="width:100%;height:300px;"></div>
  </div>
  <div class="chart-box">
    <div class="chart-title">Spending by Quarter</div>
    <div id="quarterly" style="width:100%;height:300px;"></div>
  </div>
</div>

<!-- Transaction Table -->
<div class="table-wrap">
  <div class="table-header">
    <h3>All Transactions <span id="tblCount" style="color:var(--muted);font-weight:400;font-size:0.85em;"></span></h3>
    <input class="search-box" id="searchBox" placeholder="Search payee name..." />
  </div>
  <div style="max-height: 520px; overflow-y: auto;">
    <table id="txnTable">
      <thead>
        <tr>
          <th data-col="date">Date <span class="sort-arrow"></span></th>
          <th data-col="time">Time <span class="sort-arrow"></span></th>
          <th data-col="name">Payee <span class="sort-arrow"></span></th>
          <th data-col="category">Category <span class="sort-arrow"></span></th>
          <th data-col="amount" style="text-align:right">Amount (Rs.) <span class="sort-arrow"></span></th>
        </tr>
      </thead>
      <tbody id="txnBody"></tbody>
    </table>
  </div>
  <div class="row-count" id="rowCount"></div>
</div>

<script>
const RAW = {data_json};

const COLORS = {{
  'Shopping & E-Commerce': '#6c5ce7',
  'Food & Dining':         '#e17055',
  'Groceries & Essentials':'#00b894',
  'Transport & Fuel':      '#74b9ff',
  'Travel & Stays':        '#fdcb6e',
  'Mobile Recharge':       '#a29bfe',
  'Subscriptions & Digital':'#fd79a8',
  'Credit Card Payment':   '#636e72',
  'Personal Care':         '#fab1a0',
  'Medical & Health':      '#00cec9',
  'Utilities':             '#ffeaa7',
}};

let data = RAW;
let filtered = [...data];
let sortCol = 'date';
let sortDir = -1;

// ── Init filters ──────────────────────────────────
function init() {{
  const cats = [...new Set(data.map(d => d.category))].sort();
  const sel = document.getElementById('fCategory');
  cats.forEach(c => {{
    const o = document.createElement('option');
    o.value = c; o.textContent = c;
    sel.appendChild(o);
  }});
  const months = [...new Set(data.map(d => d.month))].sort();
  document.getElementById('fFrom').value = months[0];
  document.getElementById('fTo').value = months[months.length - 1];

  sel.onchange = applyFilters;
  document.getElementById('fFrom').onchange = applyFilters;
  document.getElementById('fTo').onchange = applyFilters;
  document.getElementById('fDayType').onchange = applyFilters;
  document.getElementById('searchBox').oninput = applyFilters;

  document.querySelectorAll('#txnTable th').forEach(th => {{
    th.onclick = () => {{
      const col = th.dataset.col;
      if (sortCol === col) sortDir *= -1;
      else {{ sortCol = col; sortDir = 1; }}
      renderTable();
    }};
  }});
}}

function resetFilters() {{
  const months = [...new Set(data.map(d => d.month))].sort();
  document.getElementById('fCategory').value = 'all';
  document.getElementById('fFrom').value = months[0];
  document.getElementById('fTo').value = months[months.length - 1];
  document.getElementById('fDayType').value = 'all';
  document.getElementById('searchBox').value = '';
  applyFilters();
}}

function applyFilters() {{
  const cat = document.getElementById('fCategory').value;
  const from = document.getElementById('fFrom').value;
  const to = document.getElementById('fTo').value;
  const dayType = document.getElementById('fDayType').value;
  const search = document.getElementById('searchBox').value.toLowerCase();

  filtered = data.filter(d => {{
    if (cat !== 'all' && d.category !== cat) return false;
    if (d.month < from || d.month > to) return false;
    if (dayType === 'weekday' && d.weekend) return false;
    if (dayType === 'weekend' && !d.weekend) return false;
    if (search && !d.name.toLowerCase().includes(search)) return false;
    return true;
  }});

  renderAll();
}}

// ── Render all ────────────────────────────────────
function renderAll() {{
  renderStats();
  renderCatPie();
  renderCatBar();
  renderMonthly();
  renderTopPayees();
  renderHourly();
  renderDailyScatter();
  renderWeekend();
  renderQuarterly();
  renderTable();
}}

// ── Stats ─────────────────────────────────────────
function renderStats() {{
  const total = filtered.reduce((s, d) => s + d.amount, 0);
  const n = filtered.length;
  const avg = n ? total / n : 0;
  const payees = new Set(filtered.map(d => d.name)).size;
  const months = new Set(filtered.map(d => d.month)).size;
  const monthlyAvg = months ? total / months : 0;

  const sorted = [...filtered].sort((a, b) => b.amount - a.amount);
  const topPayee = sorted.length ? sorted[0].name : '-';
  const topPayeeAmt = sorted.length ? sorted[0].amount : 0;

  document.getElementById('statsRow').innerHTML = `
    <div class="stat-card"><div class="label">Total Spent</div><div class="value" style="color:#6c5ce7">Rs.${{total.toLocaleString('en-IN', {{maximumFractionDigits:0}})}}</div><div class="sub">${{n}} transactions</div></div>
    <div class="stat-card"><div class="label">Monthly Avg</div><div class="value" style="color:#74b9ff">Rs.${{monthlyAvg.toLocaleString('en-IN', {{maximumFractionDigits:0}})}}</div><div class="sub">${{months}} months</div></div>
    <div class="stat-card"><div class="label">Avg Transaction</div><div class="value" style="color:#00b894">Rs.${{avg.toLocaleString('en-IN', {{maximumFractionDigits:0}})}}</div><div class="sub">median: Rs.${{median(filtered).toLocaleString('en-IN')}}</div></div>
    <div class="stat-card"><div class="label">Unique Payees</div><div class="value" style="color:#fdcb6e">${{payees}}</div><div class="sub">across all categories</div></div>
    <div class="stat-card"><div class="label">Biggest Single Txn</div><div class="value" style="color:#e17055">Rs.${{sorted.length ? sorted[0].amount.toLocaleString('en-IN') : 0}}</div><div class="sub">${{sorted.length ? sorted[0].name.substring(0,25) : '-'}}</div></div>
  `;
}}

function median(arr) {{
  const vals = arr.map(d => d.amount).sort((a,b) => a - b);
  const mid = Math.floor(vals.length / 2);
  return vals.length % 2 ? vals[mid] : (vals[mid-1] + vals[mid]) / 2;
}}

// ── Category Donut ────────────────────────────────
function renderCatPie() {{
  const cats = {{}};
  filtered.forEach(d => {{ cats[d.category] = (cats[d.category] || 0) + d.amount; }});
  const sorted = Object.entries(cats).sort((a,b) => b[1] - a[1]);
  const labels = sorted.map(e => e[0]);
  const values = sorted.map(e => e[1]);
  const colors = labels.map(l => COLORS[l] || '#636e72');

  Plotly.newPlot('catPie', [{{
    type: 'pie', labels, values,
    hole: 0.45, textinfo: 'label+percent',
    textposition: 'outside', textfont: {{ size: 11 }},
    marker: {{ colors }},
    hovertemplate: '<b>%{{label}}</b><br>Rs.%{{value:,.0f}}<br>%{{percent}}<extra></extra>',
    pull: sorted.map((_, i) => i === 0 ? 0.03 : 0)
  }}], {{
    margin: {{ t: 10, b: 10, l: 10, r: 10 }},
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: {{ color: '#e4e6eb', size: 11 }},
    showlegend: true,
    legend: {{ font: {{ size: 10 }}, bgcolor: 'rgba(0,0,0,0)' }},
    annotations: [{{
      text: `Rs.${{filtered.reduce((s,d)=>s+d.amount,0).toLocaleString('en-IN',{{maximumFractionDigits:0}})}}`,
      showarrow: false, font: {{ size: 16, color: '#e4e6eb', family: 'sans-serif' }}
    }}]
  }}, {{ responsive: true, displayModeBar: false }});
}}

// ── Category Bar ──────────────────────────────────
function renderCatBar() {{
  const cats = {{}};
  filtered.forEach(d => {{ cats[d.category] = (cats[d.category] || 0) + d.amount; }});
  const sorted = Object.entries(cats).sort((a,b) => a[1] - b[1]);
  const labels = sorted.map(e => e[0]);
  const values = sorted.map(e => e[1]);
  const colors = labels.map(l => COLORS[l] || '#636e72');
  const counts = {{}};
  filtered.forEach(d => {{ counts[d.category] = (counts[d.category] || 0) + 1; }});

  Plotly.newPlot('catBar', [{{
    type: 'bar', orientation: 'h',
    y: labels, x: values,
    marker: {{ color: colors, cornerradius: 4 }},
    text: values.map((v, i) => `Rs.${{v.toLocaleString('en-IN', {{maximumFractionDigits:0}})}} (${{counts[labels[i]]}} txns)`),
    textposition: 'outside', textfont: {{ size: 10, color: '#e4e6eb' }},
    hovertemplate: '<b>%{{y}}</b><br>Rs.%{{x:,.0f}}<extra></extra>'
  }}], {{
    margin: {{ t: 10, b: 30, l: 140, r: 80 }},
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: {{ color: '#e4e6eb', size: 11 }},
    xaxis: {{ gridcolor: '#2a2d3a', tickformat: ',.0f' }},
    yaxis: {{ gridcolor: 'rgba(0,0,0,0)' }},
  }}, {{ responsive: true, displayModeBar: false }});
}}

// ── Monthly Trend ─────────────────────────────────
function renderMonthly() {{
  const monthly = {{}};
  filtered.forEach(d => {{
    if (!monthly[d.month]) monthly[d.month] = {{ total: 0, count: 0 }};
    monthly[d.month].total += d.amount;
    monthly[d.month].count++;
  }});
  const sorted = Object.entries(monthly).sort((a,b) => a[0].localeCompare(b[0]));
  const months = sorted.map(e => e[0]);
  const totals = sorted.map(e => e[1].total);
  const counts = sorted.map(e => e[1].count);
  const avg = totals.reduce((s,v) => s+v, 0) / totals.length;

  Plotly.newPlot('monthly', [
    {{
      type: 'bar', name: 'Total Spent',
      x: months, y: totals,
      marker: {{ color: '#6c5ce7', cornerradius: 3, opacity: 0.7 }},
      hovertemplate: '<b>%{{x}}</b><br>Rs.%{{y:,.0f}}<br>%{{customdata}} txns<extra></extra>',
      customdata: counts
    }},
    {{
      type: 'scatter', name: '3-mo Rolling Avg', mode: 'lines',
      x: months, y: rollingAvg(totals, 3),
      line: {{ color: '#e17055', width: 2.5 }},
      hovertemplate: '3-mo avg: Rs.%{{y:,.0f}}<extra></extra>'
    }},
    {{
      type: 'scatter', name: 'Monthly Avg', mode: 'lines',
      x: months, y: Array(months.length).fill(avg),
      line: {{ color: '#fdcb6e', width: 1.5, dash: 'dash' }},
      hovertemplate: 'Avg: Rs.%{{y:,.0f}}<extra></extra>'
    }}
  ], {{
    margin: {{ t: 10, b: 50, l: 60, r: 20 }},
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: {{ color: '#e4e6eb', size: 11 }},
    xaxis: {{ gridcolor: '#2a2d3a', tickangle: -45, dtick: 2 }},
    yaxis: {{ gridcolor: '#2a2d3a', tickformat: ',.0f' }},
    legend: {{ orientation: 'h', y: 1.12, font: {{ size: 10 }} }},
    bargap: 0.25
  }}, {{ responsive: true }});
}}

function rollingAvg(arr, n) {{
  return arr.map((_, i) => {{
    const start = Math.max(0, i - n + 1);
    const slice = arr.slice(start, i + 1);
    return slice.reduce((s,v) => s+v, 0) / slice.length;
  }});
}}

// ── Top Payees ────────────────────────────────────
function renderTopPayees() {{
  const payees = {{}};
  filtered.forEach(d => {{
    if (!payees[d.name]) payees[d.name] = {{ total: 0, count: 0, cat: d.category }};
    payees[d.name].total += d.amount;
    payees[d.name].count++;
  }});
  const sorted = Object.entries(payees).sort((a,b) => b[1].total - a[1].total).slice(0, 15).reverse();
  const names = sorted.map(e => e[0].substring(0, 30));
  const values = sorted.map(e => e[1].total);
  const cats = sorted.map(e => e[1].cat);
  const colors = cats.map(c => COLORS[c] || '#636e72');
  const texts = sorted.map((e, i) => `${{e[1].count}}x`);

  Plotly.newPlot('topPayees', [{{
    type: 'bar', orientation: 'h',
    y: names, x: values,
    marker: {{ color: colors, cornerradius: 3 }},
    text: texts, textposition: 'inside', textfont: {{ size: 10, color: '#fff' }},
    hovertemplate: '<b>%{{y}}</b><br>Rs.%{{x:,.0f}}<br>%{{text}} txns<extra></extra>'
  }}], {{
    margin: {{ t: 10, b: 30, l: 160, r: 30 }},
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: {{ color: '#e4e6eb', size: 10 }},
    xaxis: {{ gridcolor: '#2a2d3a', tickformat: ',.0f' }},
    yaxis: {{ gridcolor: 'rgba(0,0,0,0)' }},
  }}, {{ responsive: true, displayModeBar: false }});
}}

// ── Hourly ────────────────────────────────────────
function renderHourly() {{
  const hourly = Array(24).fill(0);
  const hourlyCount = Array(24).fill(0);
  filtered.forEach(d => {{
    hourly[d.hour] += d.amount;
    hourlyCount[d.hour]++;
  }});
  const labels = Array.from({{length: 24}}, (_, i) => {{
    if (i === 0) return '12a';
    if (i < 12) return i + 'a';
    if (i === 12) return '12p';
    return (i - 12) + 'p';
  }});

  Plotly.newPlot('hourly', [
    {{
      type: 'bar', name: 'Total Spent',
      x: labels, y: hourly,
      marker: {{ color: '#74b9ff', cornerradius: 3, opacity: 0.7 }},
      hovertemplate: '%{{x}}<br>Rs.%{{y:,.0f}}<extra></extra>'
    }},
    {{
      type: 'scatter', name: 'Txn Count', yaxis: 'y2',
      x: labels, y: hourlyCount, mode: 'lines+markers',
      line: {{ color: '#e17055', width: 2 }}, marker: {{ size: 5 }},
      hovertemplate: '%{{x}}<br>%{{y}} txns<extra></extra>'
    }}
  ], {{
    margin: {{ t: 10, b: 40, l: 60, r: 50 }},
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: {{ color: '#e4e6eb', size: 10 }},
    xaxis: {{ gridcolor: '#2a2d3a' }},
    yaxis: {{ gridcolor: '#2a2d3a', tickformat: ',.0f', title: 'Amount' }},
    yaxis2: {{ overlaying: 'y', side: 'right', showgrid: false, title: 'Count' }},
    legend: {{ orientation: 'h', y: 1.15, font: {{ size: 10 }} }},
  }}, {{ responsive: true, displayModeBar: false }});
}}

// ── Daily Scatter ─────────────────────────────────
function renderDailyScatter() {{
  const daily = {{}};
  filtered.forEach(d => {{
    if (!daily[d.date]) daily[d.date] = {{ total: 0, names: new Set() }};
    daily[d.date].total += d.amount;
    daily[d.date].names.add(d.name);
  }});
  const dates = Object.keys(daily).sort();
  const amounts = dates.map(d => daily[d].total);
  const texts = dates.map(d => `${{daily[d].names.size}} payees`);

  Plotly.newPlot('dailyScatter', [{{
    type: 'scatter', mode: 'markers',
    x: dates, y: amounts,
    marker: {{
      color: amounts, colorscale: [[0,'#6c5ce7'],[0.5,'#e17055'],[1,'#fdcb6e']],
      size: amounts.map(a => Math.min(12, 4 + a / 500)),
      opacity: 0.7, line: {{ width: 0.5, color: '#fff' }}
    }},
    text: texts,
    hovertemplate: '<b>%{{x}}</b><br>Rs.%{{y:,.0f}}<br>%{{text}}<extra></extra>'
  }}], {{
    margin: {{ t: 10, b: 40, l: 60, r: 20 }},
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: {{ color: '#e4e6eb', size: 11 }},
    xaxis: {{ gridcolor: '#2a2d3a', rangeslider: {{ visible: true, thickness: 0.06 }} }},
    yaxis: {{ gridcolor: '#2a2d3a', tickformat: ',.0f' }},
  }}, {{ responsive: true }});
}}

// ── Weekend ───────────────────────────────────────
function renderWeekend() {{
  const wk = {{ weekday: {{ total: 0, count: 0 }}, weekend: {{ total: 0, count: 0 }} }};
  filtered.forEach(d => {{
    const key = d.weekend ? 'weekend' : 'weekday';
    wk[key].total += d.amount;
    wk[key].count++;
  }});
  const nMonths = new Set(filtered.map(d => d.month)).size || 1;
  const wkMo = wk.weekday.total / nMonths;
  const weMo = wk.weekend.total / nMonths;

  Plotly.newPlot('weekendChart', [
    {{
      type: 'bar', name: 'Weekday',
      x: ['Total', 'Monthly Avg'], y: [wk.weekday.total, wkMo],
      marker: {{ color: '#6c5ce7', cornerradius: 4 }},
      text: [`Rs.${{wk.weekday.total.toLocaleString('en-IN',{{maximumFractionDigits:0}})}}`, `Rs.${{wkMo.toLocaleString('en-IN',{{maximumFractionDigits:0}})}}`],
      textposition: 'outside', textfont: {{ size: 10 }}
    }},
    {{
      type: 'bar', name: 'Weekend',
      x: ['Total', 'Monthly Avg'], y: [wk.weekend.total, weMo],
      marker: {{ color: '#e17055', cornerradius: 4 }},
      text: [`Rs.${{wk.weekend.total.toLocaleString('en-IN',{{maximumFractionDigits:0}})}}`, `Rs.${{weMo.toLocaleString('en-IN',{{maximumFractionDigits:0}})}}`],
      textposition: 'outside', textfont: {{ size: 10 }}
    }}
  ], {{
    margin: {{ t: 10, b: 40, l: 60, r: 20 }},
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: {{ color: '#e4e6eb', size: 11 }},
    barmode: 'group',
    xaxis: {{ gridcolor: '#2a2d3a' }},
    yaxis: {{ gridcolor: '#2a2d3a', tickformat: ',.0f' }},
    legend: {{ orientation: 'h', y: 1.15 }},
    annotations: [{{
      x: 1, y: wk.weekday.count + wk.weekend.count, xref: 'paper', yref: 'paper',
      text: `${{wk.weekday.count}} weekday txns | ${{wk.weekend.count}} weekend txns`,
      showarrow: false, font: {{ size: 9, color: '#8b8fa3' }}, yanchor: 'bottom'
    }}]
  }}, {{ responsive: true, displayModeBar: false }});
}}

// ── Quarterly ─────────────────────────────────────
function renderQuarterly() {{
  const q = {{}};
  filtered.forEach(d => {{
    if (!q[d.quarter]) q[d.quarter] = {{ total: 0, count: 0 }};
    q[d.quarter].total += d.amount;
    q[d.quarter].count++;
  }});
  const sorted = Object.entries(q).sort((a,b) => a[0].localeCompare(b[0]));
  const labels = sorted.map(e => e[0]);
  const totals = sorted.map(e => e[1].total);

  Plotly.newPlot('quarterly', [{{
    type: 'bar',
    x: labels, y: totals,
    marker: {{ color: totals.map((v,i) => {{
      const hues = ['#6c5ce7','#74b9ff','#00b894','#fdcb6e','#e17055','#a29bfe'];
      return hues[i % hues.length];
    }}), cornerradius: 4 }},
    text: totals.map(v => `Rs.${{v.toLocaleString('en-IN',{{maximumFractionDigits:0}})}}`),
    textposition: 'outside', textfont: {{ size: 10 }},
    hovertemplate: '<b>%{{x}}</b><br>Rs.%{{y:,.0f}}<extra></extra>'
  }}], {{
    margin: {{ t: 10, b: 40, l: 60, r: 20 }},
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: {{ color: '#e4e6eb', size: 11 }},
    xaxis: {{ gridcolor: '#2a2d3a' }},
    yaxis: {{ gridcolor: '#2a2d3a', tickformat: ',.0f' }},
  }}, {{ responsive: true, displayModeBar: false }});
}}

// ── Table ─────────────────────────────────────────
function renderTable() {{
  let rows = [...filtered];
  rows.sort((a, b) => {{
    let va = a[sortCol], vb = b[sortCol];
    if (sortCol === 'amount') {{ va = +va; vb = +vb; }}
    if (va < vb) return -1 * sortDir;
    if (va > vb) return 1 * sortDir;
    return 0;
  }});

  // Update sort arrows
  document.querySelectorAll('#txnTable th').forEach(th => {{
    const arrow = th.querySelector('.sort-arrow');
    if (th.dataset.col === sortCol) {{
      arrow.textContent = sortDir === 1 ? '\\u25B2' : '\\u25BC';
    }} else {{
      arrow.textContent = '';
    }}
  }});

  const catColorMap = {{
    'Shopping & E-Commerce': 'rgba(108,92,231,0.15)',
    'Food & Dining': 'rgba(225,112,85,0.15)',
    'Groceries & Essentials': 'rgba(0,184,148,0.15)',
    'Transport & Fuel': 'rgba(116,185,255,0.15)',
    'Travel & Stays': 'rgba(253,203,110,0.15)',
    'Mobile Recharge': 'rgba(162,155,254,0.15)',
    'Subscriptions & Digital': 'rgba(253,121,168,0.15)',
    'Credit Card Payment': 'rgba(99,110,114,0.15)',
    'Personal Care': 'rgba(250,177,160,0.15)',
    'Medical & Health': 'rgba(0,206,201,0.15)',
  }};

  const tbody = document.getElementById('txnBody');
  tbody.innerHTML = rows.map(d => `
    <tr style="background:${{catColorMap[d.category] || 'transparent'}}">
      <td>${{d.date}}</td>
      <td>${{d.time}}</td>
      <td>${{d.name.substring(0, 45)}}</td>
      <td><span class="cat-badge" style="background:${{COLORS[d.category] || '#636e72'}}22;color:${{COLORS[d.category] || '#636e72'}}">${{d.category}}</span></td>
      <td class="amount-cell">${{d.amount.toLocaleString('en-IN', {{maximumFractionDigits:2}})}}</td>
    </tr>
  `).join('');

  const total = rows.reduce((s, d) => s + d.amount, 0);
  document.getElementById('tblCount').textContent = `(${{rows.length}} txns)`;
  document.getElementById('rowCount').textContent = `Showing ${{rows.length}} of ${{filtered.length}} transactions &mdash; Total: Rs.${{total.toLocaleString('en-IN', {{maximumFractionDigits:0}})}}`;
}}

// ── Boot ──────────────────────────────────────────
init();
renderAll();
</script>
</body>
</html>"""

out_path = Path(__file__).parent / "spending_dashboard.html"
out_path.write_text(html, encoding="utf-8")
print(f"Dashboard generated: {out_path}")
print(f"Data points: {len(records)} transactions")
