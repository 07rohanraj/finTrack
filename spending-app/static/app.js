/* ── Spending Dashboard — Frontend Logic ────────────────
   Fetches data from server, filters client-side, renders Chart.js charts.
   Table uses pagination (no virtual scroll overhead).
   ──────────────────────────────────────────────────────── */

const CAT_COLORS = {
  'Shopping & E-Commerce': '#7c6aef',
  'Food & Dining':         '#f0574e',
  'Groceries & Essentials':'#00c9a7',
  'Transport & Fuel':      '#5b8def',
  'Travel & Stays':        '#f5a623',
  'Mobile Recharge':       '#a29bfe',
  'Subscriptions & Digital':'#e855a0',
  'Credit Card Payment':   '#636e72',
  'Personal Care':         '#fab1a0',
  'Medical & Health':      '#00cec9',
  'Utilities':             '#ffeaa7',
};

const PALETTE = ['#7c6aef','#f0574e','#00c9a7','#5b8def','#f5a623',
                 '#a29bfe','#e855a0','#636e72','#fab1a0','#00cec9','#ffeaa7'];

// ── State ───────────────────────────────────────────
let DATA = null;         // Full dataset from server
let filtered = [];       // After filters applied
let sortCol = 'date';
let sortDir = -1;
let page = 0;
const PAGE_SIZE = 50;
let charts = {};         // Chart.js instances

// ── Init ────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const resp = await fetch('/api/data');
    DATA = await resp.json();
  } catch (e) {
    document.getElementById('statsRow').innerHTML =
      '<div class="loading">Failed to load data. Is the server running?</div>';
    return;
  }

  document.getElementById('subtitle').textContent =
    `PhonePe Statement — ${DATA.summary.dateRange[0]} to ${DATA.summary.dateRange[1]} — XX6650 — Actual Spending`;

  populateFilters();
  bindEvents();
  applyFilters();
});

// ── Filters ─────────────────────────────────────────
function populateFilters() {
  const catSel = document.getElementById('fCategory');
  const tblCatSel = document.getElementById('tblCatFilter');
  DATA.summary.categories.forEach(c => {
    catSel.appendChild(opt(c, c));
    tblCatSel.appendChild(opt(c, c));
  });

  const fromSel = document.getElementById('fFrom');
  const toSel = document.getElementById('fTo');
  DATA.summary.months.forEach(m => {
    fromSel.appendChild(opt(m, m));
    toSel.appendChild(opt(m, m));
  });
  fromSel.value = DATA.summary.months[0];
  toSel.value = DATA.summary.months[DATA.summary.months.length - 1];
}

function opt(value, text) {
  const o = document.createElement('option');
  o.value = value; o.textContent = text;
  return o;
}

function bindEvents() {
  document.getElementById('fCategory').onchange = applyFilters;
  document.getElementById('fFrom').onchange = applyFilters;
  document.getElementById('fTo').onchange = applyFilters;
  document.getElementById('fDayType').onchange = applyFilters;
  document.getElementById('btnReset').onclick = resetFilters;

  document.getElementById('searchBox').addEventListener('input', debounce(() => {
    page = 0;
    renderTable();
  }, 200));

  document.getElementById('tblCatFilter').onchange = () => { page = 0; renderTable(); };

  document.querySelectorAll('thead th').forEach(th => {
    th.onclick = () => {
      const col = th.dataset.col;
      if (sortCol === col) sortDir *= -1;
      else { sortCol = col; sortDir = col === 'amount' ? -1 : 1; }
      page = 0;
      renderTable();
    };
  });

  document.getElementById('tableScroll').addEventListener('scroll', () => {
    // Lazy: nothing needed with pagination
  });
}

function resetFilters() {
  document.getElementById('fCategory').value = 'all';
  document.getElementById('fFrom').value = DATA.summary.months[0];
  document.getElementById('fTo').value = DATA.summary.months[DATA.summary.months.length - 1];
  document.getElementById('fDayType').value = 'all';
  document.getElementById('searchBox').value = '';
  document.getElementById('tblCatFilter').value = 'all';
  page = 0;
  applyFilters();
}

function applyFilters() {
  const cat = document.getElementById('fCategory').value;
  const from = document.getElementById('fFrom').value;
  const to = document.getElementById('fTo').value;
  const dayType = document.getElementById('fDayType').value;

  filtered = DATA.transactions.filter(d => {
    if (cat !== 'all' && d.category !== cat) return false;
    if (d.month < from || d.month > to) return false;
    if (dayType === 'weekday' && d.weekend) return false;
    if (dayType === 'weekend' && !d.weekend) return false;
    return true;
  });

  page = 0;
  renderAll();
}

// ── Render Everything ───────────────────────────────
function renderAll() {
  renderStats();
  renderMonthly();
  renderCategory();
  renderPayees();
  renderWeekend();
  renderHourly();
  renderQuarterly();
  renderDow();
  renderTable();
}

// ── Stats ───────────────────────────────────────────
function renderStats() {
  const total = filtered.reduce((s, d) => s + d.amount, 0);
  const n = filtered.length;
  const months = new Set(filtered.map(d => d.month)).size;
  const avg = n ? total / n : 0;
  const monthly = months ? total / months : 0;
  const payees = new Set(filtered.map(d => d.name)).size;
  const sorted = [...filtered].sort((a, b) => b.amount - a.amount);

  document.getElementById('statsRow').innerHTML = `
    <div class="stat"><div class="label">Total Spent</div>
      <div class="value" style="color:var(--accent)">Rs.${fmtI(total)}</div>
      <div class="sub">${n} txns</div></div>
    <div class="stat"><div class="label">Monthly Avg</div>
      <div class="value" style="color:var(--accent2)">Rs.${fmtI(monthly)}</div>
      <div class="sub">${months} months</div></div>
    <div class="stat"><div class="label">Avg Transaction</div>
      <div class="value" style="color:var(--green)">Rs.${fmtI(avg)}</div>
      <div class="sub">median Rs.${fmtI(median(filtered))}</div></div>
    <div class="stat"><div class="label">Unique Payees</div>
      <div class="value" style="color:var(--orange)">${payees}</div>
      <div class="sub">across all categories</div></div>
    <div class="stat"><div class="label">Biggest Transaction</div>
      <div class="value" style="color:var(--red)">Rs.${fmtI(sorted[0]?.amount || 0)}</div>
      <div class="sub">${(sorted[0]?.name || '-').substring(0, 22)}</div></div>
  `;
}

function median(arr) {
  const v = arr.map(d => d.amount).sort((a, b) => a - b);
  const m = Math.floor(v.length / 2);
  return v.length % 2 ? v[m] : (v[m-1] + v[m]) / 2;
}

// ── Chart: Monthly ──────────────────────────────────
function renderMonthly() {
  const map = {};
  filtered.forEach(d => {
    if (!map[d.month]) map[d.month] = { total: 0, count: 0 };
    map[d.month].total += d.amount;
    map[d.month].count++;
  });
  const keys = Object.keys(map).sort();
  const totals = keys.map(k => map[k].total);
  const counts = keys.map(k => map[k].count);
  const rolling = rollingAvg(totals, 3);
  const avgLine = totals.reduce((s,v)=>s+v,0) / totals.length;

  const ctx = document.getElementById('chartMonthly');
  if (charts.monthly) charts.monthly.destroy();
  charts.monthly = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: keys.map(k => k.substring(2)),
      datasets: [
        {
          label: 'Spent',
          data: totals,
          backgroundColor: 'rgba(124,106,239,0.6)',
          borderRadius: 4,
          order: 2,
          yAxisID: 'y',
        },
        {
          label: '3-mo avg',
          data: rolling,
          type: 'line',
          borderColor: '#f0574e',
          borderWidth: 2.5,
          pointRadius: 0,
          tension: 0.3,
          fill: false,
          order: 1,
          yAxisID: 'y',
        },
        {
          label: 'Monthly avg',
          data: Array(keys.length).fill(avgLine),
          type: 'line',
          borderColor: 'rgba(245,166,35,0.5)',
          borderWidth: 1.5,
          borderDash: [6, 4],
          pointRadius: 0,
          fill: false,
          order: 0,
          yAxisID: 'y',
        },
        {
          label: 'Txn Count',
          data: counts,
          type: 'line',
          borderColor: '#00c9a7',
          borderWidth: 1.5,
          pointRadius: 2,
          pointBackgroundColor: '#00c9a7',
          tension: 0.3,
          fill: false,
          order: 1,
          yAxisID: 'y1',
        }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        tooltip: {
          callbacks: {
            label: (ctx) => {
              if (ctx.datasetIndex === 0) return `Rs.${fmtI(ctx.raw)} (${counts[ctx.dataIndex]} txns)`;
              if (ctx.datasetIndex === 3) return `${ctx.raw} txns`;
              return `${ctx.dataset.label}: Rs.${fmtI(ctx.raw)}`;
            }
          }
        },
        legend: { labels: { color: '#888', boxWidth: 12, font: { size: 11 } } }
      },
      scales: {
        x: { ticks: { color: '#666', font: { size: 10 }, maxRotation: 45 }, grid: { color: '#1e2035' } },
        y: { position: 'left', ticks: { color: '#666', callback: v => fmtShort(v) }, grid: { color: '#1e2035' } },
        y1: { position: 'right', ticks: { color: '#00c9a7', font: { size: 10 } }, grid: { display: false } }
      }
    }
  });
}

// ── Chart: Category Doughnut ────────────────────────
function renderCategory() {
  const cats = {};
  filtered.forEach(d => { cats[d.category] = (cats[d.category] || 0) + d.amount; });
  const sorted = Object.entries(cats).sort((a, b) => b[1] - a[1]);
  const labels = sorted.map(e => e[0]);
  const values = sorted.map(e => e[1]);
  const colors = labels.map(l => CAT_COLORS[l] || '#636e72');
  const total = values.reduce((s, v) => s + v, 0);

  const ctx = document.getElementById('chartCategory');
  if (charts.category) charts.category.destroy();
  charts.category = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: colors,
        borderWidth: 2,
        borderColor: '#1a1d2e',
        hoverOffset: 8,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: '55%',
      plugins: {
        legend: { position: 'right', labels: { color: '#aaa', font: { size: 10 }, boxWidth: 10, padding: 8 } },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const pct = ((ctx.raw / total) * 100).toFixed(1);
              return `${ctx.label}: Rs.${fmtI(ctx.raw)} (${pct}%)`;
            }
          }
        }
      }
    },
    plugins: [{
      id: 'centerText',
      afterDraw(chart) {
        const { ctx: c, width, height } = chart;
        c.save();
        c.textAlign = 'center'; c.textBaseline = 'middle';
        const cx = width / 2, cy = height / 2;
        c.fillStyle = '#e2e4ea'; c.font = 'bold 16px Inter, sans-serif';
        c.fillText(`Rs.${fmtShort(total)}`, cx, cy - 8);
        c.fillStyle = '#6c7086'; c.font = '11px Inter, sans-serif';
        c.fillText(`${labels.length} categories`, cx, cy + 12);
        c.restore();
      }
    }]
  });
}

// ── Chart: Top Payees ───────────────────────────────
function renderPayees() {
  const payees = {};
  filtered.forEach(d => {
    if (!payees[d.name]) payees[d.name] = { total: 0, count: 0, cat: d.category };
    payees[d.name].total += d.amount;
    payees[d.name].count++;
  });
  const sorted = Object.entries(payees).sort((a, b) => b[1].total - a[1].total).slice(0, 12);
  const names = sorted.map(e => e[0].length > 22 ? e[0].substring(0, 20) + '..' : e[0]);
  const values = sorted.map(e => e[1].total);
  const colors = sorted.map(e => CAT_COLORS[e[1].cat] || '#636e72');

  const ctx = document.getElementById('chartPayees');
  if (charts.payees) charts.payees.destroy();
  charts.payees = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: names.reverse(),
      datasets: [{
        data: values.reverse(),
        backgroundColor: colors.reverse(),
        borderRadius: 4,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => sorted.reverse()[items[0].dataIndex]?.[0] || '',
            label: (ctx) => {
              const e = sorted[ctx.dataIndex];
              return `Rs.${fmtI(ctx.raw)} (${e[1].count}x)`;
            }
          }
        }
      },
      scales: {
        x: { ticks: { color: '#666', callback: v => fmtShort(v) }, grid: { color: '#1e2035' } },
        y: { ticks: { color: '#aaa', font: { size: 10 } }, grid: { display: false } }
      }
    }
  });
}

// ── Chart: Weekend ──────────────────────────────────
function renderWeekend() {
  const wk = { weekday: { total: 0, count: 0 }, weekend: { total: 0, count: 0 } };
  filtered.forEach(d => {
    const k = d.weekend ? 'weekend' : 'weekday';
    wk[k].total += d.amount;
    wk[k].count++;
  });

  const ctx = document.getElementById('chartWeekend');
  if (charts.weekend) charts.weekend.destroy();
  charts.weekend = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Total Spent', 'Avg per Txn'],
      datasets: [
        {
          label: 'Weekday',
          data: [wk.weekday.total, wk.weekday.count ? wk.weekday.total / wk.weekday.count : 0],
          backgroundColor: '#7c6aef',
          borderRadius: 6,
        },
        {
          label: 'Weekend',
          data: [wk.weekend.total, wk.weekend.count ? wk.weekend.total / wk.weekend.count : 0],
          backgroundColor: '#f0574e',
          borderRadius: 6,
        }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#aaa', boxWidth: 10 } },
        tooltip: {
          callbacks: {
            afterLabel: (ctx) => {
              const k = ctx.datasetIndex === 0 ? 'weekday' : 'weekend';
              return `${wk[k].count} txns`;
            },
            label: (ctx) => `Rs.${fmtI(ctx.raw)}`
          }
        }
      },
      scales: {
        x: { ticks: { color: '#888' }, grid: { display: false } },
        y: { ticks: { color: '#666', callback: v => fmtShort(v) }, grid: { color: '#1e2035' } }
      }
    }
  });
}

// ── Chart: Hourly ───────────────────────────────────
function renderHourly() {
  const hourly = Array(24).fill(0);
  const hourlyCount = Array(24).fill(0);
  filtered.forEach(d => { hourly[d.hour] += d.amount; hourlyCount[d.hour]++; });
  const labels = Array.from({ length: 24 }, (_, i) => {
    if (i === 0) return '12a';
    if (i < 12) return i + 'a';
    if (i === 12) return '12p';
    return (i - 12) + 'p';
  });

  const ctx = document.getElementById('chartHourly');
  if (charts.hourly) charts.hourly.destroy();
  charts.hourly = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Amount',
        data: hourly,
        backgroundColor: hourly.map((v, i) => i >= 6 && i < 18 ? '#5b8def' : '#7c6aef'),
        borderRadius: 3,
        yAxisID: 'y',
      }, {
        label: 'Count',
        data: hourlyCount,
        type: 'line',
        borderColor: '#f0574e',
        borderWidth: 1.5,
        pointRadius: 2,
        pointBackgroundColor: '#f0574e',
        fill: false,
        yAxisID: 'y1',
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { labels: { color: '#888', boxWidth: 10, font: { size: 10 } } },
        tooltip: {
          callbacks: {
            label: (ctx) => ctx.datasetIndex === 0 ? `Rs.${fmtI(ctx.raw)}` : `${ctx.raw} txns`
          }
        }
      },
      scales: {
        x: { ticks: { color: '#666', font: { size: 9 } }, grid: { color: '#1e2035' } },
        y: { ticks: { color: '#666', callback: v => fmtShort(v) }, grid: { color: '#1e2035' } },
        y1: { position: 'right', ticks: { color: '#f0574e', font: { size: 10 } }, grid: { display: false } }
      }
    }
  });
}

// ── Chart: Quarterly ────────────────────────────────
function renderQuarterly() {
  const q = {};
  filtered.forEach(d => {
    if (!q[d.quarter]) q[d.quarter] = { total: 0, count: 0 };
    q[d.quarter].total += d.amount;
    q[d.quarter].count++;
  });
  const sorted = Object.entries(q).sort((a, b) => a[0].localeCompare(b[0]));
  const labels = sorted.map(e => e[0]);
  const totals = sorted.map(e => e[1].total);

  const ctx = document.getElementById('chartQuarterly');
  if (charts.quarterly) charts.quarterly.destroy();
  charts.quarterly = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data: totals,
        backgroundColor: labels.map((_, i) => PALETTE[i % PALETTE.length]),
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `Rs.${fmtI(ctx.raw)} (${sorted[ctx.dataIndex][1].count} txns)`
          }
        }
      },
      scales: {
        x: { ticks: { color: '#888' }, grid: { display: false } },
        y: { ticks: { color: '#666', callback: v => fmtShort(v) }, grid: { color: '#1e2035' } }
      }
    }
  });
}

// ── Chart: Day of Week ──────────────────────────────
function renderDow() {
  const dow = Array(7).fill(null).map(() => ({ total: 0, count: 0 }));
  const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  filtered.forEach(d => { dow[d.dayNum].total += d.amount; dow[d.dayNum].count++; });

  const ctx = document.getElementById('chartDow');
  if (charts.dow) charts.dow.destroy();
  charts.dow = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: dayNames,
      datasets: [{
        data: dow.map(d => d.total),
        backgroundColor: dow.map((_, i) => i >= 5 ? '#f0574e' : '#7c6aef'),
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const d = dow[ctx.dataIndex];
              return `Rs.${fmtI(ctx.raw)} (${d.count} txns, avg Rs.${fmtI(d.count ? d.total / d.count : 0)})`;
            }
          }
        }
      },
      scales: {
        x: { ticks: { color: '#888' }, grid: { display: false } },
        y: { ticks: { color: '#666', callback: v => fmtShort(v) }, grid: { color: '#1e2035' } }
      }
    }
  });
}

// ── Table ───────────────────────────────────────────
function renderTable() {
  const search = document.getElementById('searchBox').value.toLowerCase();
  const tblCat = document.getElementById('tblCatFilter').value;

  let rows = filtered.filter(d => {
    if (tblCat !== 'all' && d.category !== tblCat) return false;
    if (search && !d.name.toLowerCase().includes(search) && !d.category.toLowerCase().includes(search)) return false;
    return true;
  });

  rows.sort((a, b) => {
    let va = a[sortCol], vb = b[sortCol];
    if (sortCol === 'amount') { va = +va; vb = +vb; }
    if (va < vb) return -1 * sortDir;
    if (va > vb) return 1 * sortDir;
    return 0;
  });

  // Sort arrows
  document.querySelectorAll('thead th').forEach(th => {
    const arrow = th.querySelector('.arrow');
    arrow.textContent = th.dataset.col === sortCol ? (sortDir === 1 ? ' \u25B2' : ' \u25BC') : '';
  });

  const totalPages = Math.ceil(rows.length / PAGE_SIZE);
  if (page >= totalPages) page = Math.max(0, totalPages - 1);
  const start = page * PAGE_SIZE;
  const pageRows = rows.slice(start, start + PAGE_SIZE);

  const tbody = document.getElementById('txnBody');
  tbody.innerHTML = pageRows.map(d => {
    const col = CAT_COLORS[d.category] || '#636e72';
    return `<tr>
      <td>${d.date}</td>
      <td>${d.time}</td>
      <td title="${esc(d.name)}">${esc(d.name.length > 38 ? d.name.substring(0, 36) + '..' : d.name)}</td>
      <td><span class="cat-tag" style="background:${col}18;color:${col}">${d.category}</span></td>
      <td class="num">${d.amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</td>
    </tr>`;
  }).join('');

  const totalAmt = rows.reduce((s, d) => s + d.amount, 0);
  document.getElementById('tblCount').textContent = `(${rows.length} txns)`;
  document.getElementById('tblInfo').textContent =
    `Showing ${start + 1}-${Math.min(start + PAGE_SIZE, rows.length)} of ${rows.length}  |  Total: Rs.${fmtI(totalAmt)}`;

  renderPagination(totalPages);
}

function renderPagination(totalPages) {
  const el = document.getElementById('pagination');
  if (totalPages <= 1) { el.innerHTML = ''; return; }

  let html = '';
  html += `<button ${page === 0 ? 'disabled' : ''} onclick="goPage(0)">&laquo;</button>`;
  html += `<button ${page === 0 ? 'disabled' : ''} onclick="goPage(${page - 1})">&lsaquo;</button>`;

  const range = 3;
  let startP = Math.max(0, page - range);
  let endP = Math.min(totalPages - 1, page + range);
  if (startP > 0) html += `<button onclick="goPage(0)">1</button><button disabled>...</button>`;
  for (let i = startP; i <= endP; i++) {
    html += `<button class="${i === page ? 'active' : ''}" onclick="goPage(${i})">${i + 1}</button>`;
  }
  if (endP < totalPages - 1) html += `<button disabled>...</button><button onclick="goPage(${totalPages - 1})">${totalPages}</button>`;

  html += `<button ${page >= totalPages - 1 ? 'disabled' : ''} onclick="goPage(${page + 1})">&rsaquo;</button>`;
  html += `<button ${page >= totalPages - 1 ? 'disabled' : ''} onclick="goPage(${totalPages - 1})">&raquo;</button>`;
  el.innerHTML = html;
}

function goPage(p) { page = p; renderTable(); document.getElementById('tableScroll').scrollTop = 0; }

// ── Helpers ─────────────────────────────────────────
function fmtI(n) { return Math.round(n).toLocaleString('en-IN'); }
function fmtShort(n) {
  if (n >= 100000) return (n / 100000).toFixed(1) + 'L';
  if (n >= 1000) return (n / 1000).toFixed(0) + 'K';
  return Math.round(n).toString();
}
function rollingAvg(arr, n) {
  return arr.map((_, i) => {
    const s = Math.max(0, i - n + 1);
    const sl = arr.slice(s, i + 1);
    return sl.reduce((a, b) => a + b, 0) / sl.length;
  });
}
function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

// Expose for inline onclick
window.goPage = goPage;
