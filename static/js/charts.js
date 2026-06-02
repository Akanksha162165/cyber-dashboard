const COLORS = ['#00e5ff','#a855f7','#f43f5e','#10b981','#f97316',
                '#fbbf24','#60a5fa','#f472b6','#34d399','#fb923c'];
const SEV_ORDER  = ['Critical','High','Medium','Low'];
const SEV_COLORS = { Critical:'#f43f5e', High:'#f97316', Medium:'#fbbf24', Low:'#10b981' };
const STATUS_COLORS = { Blocked:'#10b981', Mitigated:'#00e5ff', Ongoing:'#f97316', Resolved:'#a855f7' };

Chart.defaults.color       = '#4d7096';
Chart.defaults.borderColor = '#1a3352';
Chart.defaults.font.family = 'Segoe UI, system-ui, sans-serif';
Chart.defaults.font.size   = 11;

Chart.register({
  id: 'doughnutCenter',
  afterDraw(chart) {
    if (chart.config.type !== 'doughnut') return;
    const { ctx, chartArea } = chart;
    if (!chartArea) return;
    const total = chart.data.datasets[0].data.reduce((a,b) => a+b, 0);
    const cx = (chartArea.left + chartArea.right)  / 2;
    const cy = (chartArea.top  + chartArea.bottom) / 2;
    ctx.save();
    ctx.font = 'bold 22px Segoe UI, system-ui, sans-serif';
    ctx.fillStyle = '#c5d5ed';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(total.toLocaleString(), cx, cy - 10);
    ctx.font = '11px Segoe UI, system-ui, sans-serif';
    ctx.fillStyle = '#4d7096';
    ctx.fillText(chart.config.options._centerLabel || 'Total', cx, cy + 12);
    ctx.restore();
  }
});

Chart.register({
  id: 'barValue',
  afterDatasetsDraw(chart) {
    if (chart.config.type !== 'bar') return;
    const { ctx } = chart;
    chart.data.datasets.forEach((ds, i) => {
      chart.getDatasetMeta(i).data.forEach((bar, j) => {
        const v = ds.data[j];
        if (v == null) return;
        const isH = chart.config.options.indexAxis === 'y';
        ctx.save();
        ctx.font = 'bold 10px Segoe UI';
        ctx.fillStyle = '#8aaccc';
        ctx.textAlign = isH ? 'left' : 'center';
        ctx.textBaseline = isH ? 'middle' : 'bottom';
        if (isH) ctx.fillText(v.toLocaleString(), bar.x + 5, bar.y);
        else     ctx.fillText(v.toLocaleString(), bar.x, bar.y - 5);
        ctx.restore();
      });
    });
  }
});

const charts = {};
function destroyChart(id) { if (charts[id]) { charts[id].destroy(); delete charts[id]; } }

function showSpinner() { document.getElementById('spinner-overlay').classList.remove('hidden'); }
function hideSpinner() { document.getElementById('spinner-overlay').classList.add('hidden'); }

function animateCount(el, target, suffix = '') {
  if (!el) return;
  let cur = 0;
  const step = target / 60;
  const t = setInterval(() => {
    cur = Math.min(cur + step, target);
    el.textContent = Math.floor(cur).toLocaleString() + suffix;
    if (cur >= target) clearInterval(t);
  }, 16);
}

function updateTimestamp() {
  const el = document.getElementById('last-updated');
  if (el) el.textContent = 'Updated: ' + new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
}

function buildChart(id, type, labels, data, opts = {}) {
  destroyChart(id);
  const ctx = document.getElementById(id);
  if (!ctx) return;
  const colorSet = opts.colors || COLORS;
  let bgColor;
  if (type === 'line' && opts.singleColor) {
    const g = ctx.getContext('2d').createLinearGradient(0, 0, 0, ctx.offsetHeight || 220);
    g.addColorStop(0,   opts.singleColor + '88');
    g.addColorStop(0.5, opts.singleColor + '33');
    g.addColorStop(1,   opts.singleColor + '00');
    bgColor = g;
  } else {
    bgColor = opts.singleColor ? opts.singleColor+'99' : colorSet.slice(0, data.length);
  }
  charts[id] = new Chart(ctx, {
    type,
    data: {
      labels,
      datasets: [{
        label: opts.label || '', data,
        backgroundColor:      bgColor,
        borderColor:          opts.singleColor ? opts.singleColor : colorSet.slice(0, data.length),
        borderWidth:          type==='line' ? 2.5 : 0,
        borderRadius:         type==='bar'  ? 6   : 0,
        fill:                 opts.fill ?? false,
        tension:              0.4,
        pointBackgroundColor: opts.singleColor || '#00e5ff',
        pointBorderColor:     '#060a14',
        pointBorderWidth:     2,
        pointRadius:          type==='line' ? 4 : 0,
        pointHoverRadius:     type==='line' ? 7 : 0,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      animation:  { duration: 700, easing: 'easeOutQuart' },
      indexAxis:  opts.horizontal ? 'y' : 'x',
      _centerLabel: opts.centerLabel || 'Total',
      plugins: {
        legend: {
          display:  opts.legend ?? false,
          position: opts.legendPos || 'right',
          labels:   { color:'#7a9abf', boxWidth:12, padding:14, font:{size:11}, usePointStyle:true },
        },
        tooltip: {
          backgroundColor:'#0d1726', borderColor:'#1a3352', borderWidth:1,
          titleColor:'#00e5ff', bodyColor:'#c5d5ed', padding:10, cornerRadius:8,
          callbacks: {
            label: (item) => {
              const v = item.raw;
              const total = item.dataset.data.reduce((a,b) => a+b, 0);
              const pct = total > 0 ? ((v/total)*100).toFixed(1) : 0;
              return type==='doughnut' ? ` ${v.toLocaleString()} (${pct}%)` : ` ${v.toLocaleString()}`;
            }
          }
        },
      },
      scales: (type==='doughnut'||type==='pie') ? {} : {
        x: { ticks:{color:'#4d7096',maxRotation:opts.horizontal?0:30,maxTicksLimit:type==='line'?8:20}, grid:{color:'#0f1e30'} },
        y: { ticks:{color:'#4d7096'}, grid:{color:'#0f1e30'}, beginAtZero:true },
      },
    },
  });
}

function renderCharts(data) {
  buildChart('chartAttack','doughnut',
    Object.keys(data.attack_types), Object.values(data.attack_types),
    { legend:true, legendPos:'right', centerLabel:'Incidents' });

  const months    = Object.keys(data.monthly_trend || {});
  const shortMths = months.map(m => {
    const [y,mo] = m.split('-');
    return new Date(y,mo-1).toLocaleString('default',{month:'short',year:'2-digit'});
  });
  buildChart('chartTrend','line', shortMths, Object.values(data.monthly_trend||{}),
    { singleColor:'#00e5ff', fill:true, label:'Attacks' });

  const srcRaw = data.source_countries || {};
  const srcFiltered = Object.fromEntries(
    Object.entries(srcRaw).filter(([k])=>k!=='Unknown').sort((a,b)=>b[1]-a[1]).slice(0,10)
  );
  const srcMax = Math.max(...Object.values(srcFiltered), 1);
  const srcColors = Object.values(srcFiltered).map(v => {
    const r = v/srcMax;
    if (r>0.7) return '#f43f5e';
    if (r>0.4) return '#f97316';
    if (r>0.2) return '#fbbf24';
    return '#10b981';
  });
  buildChart('chartCountry','bar', Object.keys(srcFiltered), Object.values(srcFiltered),
    { colors:srcColors, horizontal:true, label:'Incidents' });

  buildChart('chartSector','bar',
    Object.keys(data.sectors||{}), Object.values(data.sectors||{}),
    { label:'Incidents' });

  const sevData    = data.severity || {};
  const sevOrdered = SEV_ORDER.filter(k => sevData[k] != null);
  buildChart('chartSeverity','doughnut',
    sevOrdered, sevOrdered.map(k=>sevData[k]),
    { colors:sevOrdered.map(k=>SEV_COLORS[k]), legend:true, legendPos:'right', centerLabel:'By Severity' });

  const stL = Object.keys(data.statuses||{});
  buildChart('chartStatus','doughnut', stL, Object.values(data.statuses||{}),
    { colors:stL.map(l=>STATUS_COLORS[l]||'#888'), legend:true, legendPos:'right', centerLabel:'By Status' });

  animateCount(document.getElementById('s-total'),    data.total_threats   || 0);
  animateCount(document.getElementById('s-blocked'),  data.blocked_attacks || 0);
  animateCount(document.getElementById('s-breaches'), data.breach_count    || 0);
  const rEl = document.getElementById('s-rate');
  if (rEl) rEl.textContent = (data.block_rate||0) + '%';
  const dEl = document.getElementById('s-duration');
  if (dEl) dEl.textContent = (data.avg_duration_min||0) + ' min';
  if (data.recent_incidents) renderRecentTable(data.recent_incidents);
  updateTimestamp();
}

function renderRecentTable(incidents) {
  const tbody = document.getElementById('recent-tbody');
  if (!tbody) return;
  if (!incidents || incidents.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--text-dim);padding:16px">No recent incidents.</td></tr>`;
    return;
  }
  tbody.innerHTML = incidents.map((r,i) => `
    <tr class="${i%2===0?'row-even':'row-odd'}">
      <td class="row-num">${i+1}</td>
      <td style="font-family:monospace;color:var(--text-muted);font-size:11px">${r.incident_id||'—'}</td>
      <td>${r.date||'—'}</td>
      <td>${r.attack_type||'—'}</td>
      <td>${r.source_country||'—'} <span style="color:var(--accent2)">→</span> ${r.target_country||'—'}</td>
      <td>${r.sector||'—'}</td>
      <td>${badge(r.severity)} ${badge(r.status)}</td>
    </tr>
  `).join('');
}

function viewAllIncidents() {
  const btn = document.querySelector('.tab-btn:nth-child(3)');
  if (btn) showTab('incidents', btn);
  window.scrollTo({ top:0, behavior:'smooth' });
}


let leafletMap = null;
let mapCircles = [];

const COUNTRY_COORDS = {
  'Russia':[61,105],'China':[35,105],'United States':[38,-97],'North Korea':[40,127],
  'Iran':[32,53],'Ukraine':[49,32],'Brazil':[-10,-55],'India':[20,78],'Germany':[51,10],
  'United Kingdom':[55,-3],'France':[46,2],'Japan':[36,138],'Australia':[-25,133],
  'Canada':[56,-106],'South Korea':[36,128],'Italy':[42,12],'Netherlands':[52,5],
  'Spain':[40,-4],'Singapore':[1,104],'UAE':[24,54],'Pakistan':[30,69],
  'Israel':[31,35],'Turkey':[39,35],'Saudi Arabia':[24,45],'Mexico':[23,-102],
  'Indonesia':[-5,120],'Argentina':[-34,-64],'South Africa':[-29,25],'Poland':[52,20],
};

function getBubbleColor(ratio) {
  if (ratio > 0.7) return { fill:'#f43f5e', border:'#f43f5e' };
  if (ratio > 0.4) return { fill:'#f97316', border:'#f97316' };
  if (ratio > 0.2) return { fill:'#fbbf24', border:'#fbbf24' };
  return { fill:'#10b981', border:'#10b981' };
}

async function renderMap() {
  showSpinner();
  try {
    const res  = await fetch('/api/map-data');
    const data = await res.json();

    const combined = Object.fromEntries(
      Object.entries(data.combined || {}).filter(([k]) => k !== 'Unknown')
    );
    const maxVal = Math.max(...Object.values(combined), 1);

    if (!leafletMap) {
      leafletMap = L.map('leaflet-map', {
        center:[20,10], zoom:2, zoomControl:true,
        scrollWheelZoom:true, minZoom:1, maxZoom:6,
      });
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution:'© OpenStreetMap © CARTO',
        subdomains:'abcd', maxZoom:20,
      }).addTo(leafletMap);
    }

    mapCircles.forEach(c => c.remove());
    mapCircles = [];

    Object.entries(combined)
      .filter(([c]) => COUNTRY_COORDS[c])
      .forEach(([country, count]) => {
        const [lat, lng] = COUNTRY_COORDS[country];
        const ratio  = count / maxVal;
        const color  = getBubbleColor(ratio);
        const radius = Math.max(150000, ratio * 1200000);

        const circle = L.circle([lat, lng], {
          color:       color.border,
          fillColor:   color.fill,
          fillOpacity: 0.45,
          weight:      1.5,
          radius:      radius,
        }).addTo(leafletMap);

        const total = Object.values(combined).reduce((a,b) => a+b, 0);
        const pct = ((count / total) * 100).toFixed(1);
        circle.bindPopup(`
          <div style="font-family:Segoe UI,sans-serif;min-width:160px">
            <div style="font-weight:700;font-size:13px;margin-bottom:6px">🌐 ${country}</div>
            <div style="font-size:12px">Attacks: <b>${count.toLocaleString()}</b></div>
            <div style="font-size:12px">Share: <b>${pct}%</b></div>
          </div>
        `);

        if (ratio > 0.15) {
          circle.bindTooltip(country, {
            permanent:true, direction:'center', className:'map-label'
          });
        }
        mapCircles.push(circle);
      });

    const srcF = Object.fromEntries(
      Object.entries(data.source_countries||{}).filter(([k])=>k!=='Unknown').sort((a,b)=>b[1]-a[1]).slice(0,8)
    );
    const tgtF = Object.fromEntries(
      Object.entries(data.target_countries||{}).filter(([k])=>k!=='Unknown').sort((a,b)=>b[1]-a[1]).slice(0,8)
    );
    buildChart('chartSrcBar','bar',Object.keys(srcF),Object.values(srcF),{singleColor:'#f43f5e',horizontal:true,label:'Origin attacks'});
    buildChart('chartTgtBar','bar',Object.keys(tgtF),Object.values(tgtF),{singleColor:'#00e5ff',horizontal:true,label:'Received attacks'});

    setTimeout(() => leafletMap.invalidateSize(), 200);
  } finally {
    hideSpinner();
  }
}

function showTab(name, btn) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.add('hidden'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.remove('hidden');
  btn.classList.add('active');
  if (name === 'map')       renderMap();
  if (name === 'incidents') loadTable();
}

function toggleTheme() {
  const html = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';
  html.setAttribute('data-theme', isDark ? 'light' : 'dark');
  document.getElementById('theme-toggle').textContent = isDark ? '☀️' : '🌙';
}

let alertPanelOpen = false;

async function toggleAlerts() {
  const panel = document.getElementById('alert-panel');
  alertPanelOpen = !alertPanelOpen;
  panel.classList.toggle('hidden', !alertPanelOpen);
  if (alertPanelOpen) await loadAlerts();
}

async function loadAlerts() {
  const res  = await fetch('/api/alerts');
  const data = await res.json();
  const list = document.getElementById('alert-list');
  const cntEl = document.getElementById('alert-count');
  if (data.count > 0) {
    cntEl.textContent = data.count;
    cntEl.classList.remove('hidden');
    document.getElementById('alert-banner').classList.remove('hidden');
    document.getElementById('alert-text').textContent =
      `⚠️  ${data.count} active Critical/High threat${data.count>1?'s':''} — immediate attention required`;
  }
  if (!data.alerts || data.alerts.length === 0) {
    list.innerHTML = '<div style="color:var(--text-dim);padding:14px;text-align:center;font-size:12px">✅ No active critical alerts</div>';
    return;
  }
  list.innerHTML = data.alerts.map(a => `
    <div class="alert-item">
      <div class="alert-item-top">
        <span class="badge badge-${a.severity.toLowerCase()}">${a.severity}</span>
        <span class="badge badge-ongoing">Ongoing</span>
      </div>
      <div class="alert-item-text">
        ${a.attack_type} — ${a.source_country} → ${a.target_country}<br>
        Sector: ${a.sector} &nbsp;|&nbsp; ${a.date}
      </div>
    </div>
  `).join('');
}

document.addEventListener('click', (e) => {
  if (alertPanelOpen && !e.target.closest('#alert-panel') && !e.target.closest('#alert-bell')) {
    document.getElementById('alert-panel').classList.add('hidden');
    alertPanelOpen = false;
  }
});

let currentPage = 1, searchTerm = '';

function getFilters() {
  return {
    attack_type:    document.getElementById('f-attack').value,
    sector:         document.getElementById('f-sector').value,
    severity:       document.getElementById('f-severity').value,
    source_country: document.getElementById('f-country').value,
    year:           (document.getElementById('f-year')||{}).value || '',
    month:          (document.getElementById('f-month')||{}).value || '',
  };
}

function buildQuery(filters) {
  const p = new URLSearchParams();
  Object.entries(filters).forEach(([k,v]) => { if (v) p.append(k,v); });
  return p.toString();
}

async function applyFilters() {
  showSpinner();
  if (leafletMap) { mapCircles.forEach(c=>c.remove()); mapCircles=[]; }
  try {
    const q    = buildQuery(getFilters());
    const res  = await fetch('/api/data' + (q?'?'+q:''));
    const data = await res.json();
    renderCharts(data);
    currentPage = 1;
    if (!document.getElementById('tab-incidents').classList.contains('hidden')) loadTable();
  } finally {
    hideSpinner();
  }
}

function resetFilters() {
  ['f-attack','f-sector','f-severity','f-country','f-year','f-month'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  applyFilters();
}

async function loadFilterOptions() {
  const res  = await fetch('/api/filter-options');
  const opts = await res.json();
  const add  = (id, list, labelKey=null) => {
    const el = document.getElementById(id);
    if (!el) return;
    list.forEach(v => {
      const o = document.createElement('option');
      if (labelKey) { o.value=v.value; o.textContent=v[labelKey]; }
      else          { o.value=v;       o.textContent=v; }
      el.appendChild(o);
    });
  };
  add('f-attack',   opts.attack_types);
  add('f-sector',   opts.sectors);
  add('f-severity', opts.severities);
  add('f-country',  opts.source_countries);
  add('f-year',     opts.years  || []);
  add('f-month',    opts.months || [], 'label');
}

function exportCSV() {
  const q = buildQuery(getFilters());
  window.location.href = '/api/export/csv' + (q?'?'+q:'');
}

function badge(text) {
  if (!text||text==='—') return text||'—';
  const cls = {
    Critical:'badge-critical', High:'badge-high', Medium:'badge-medium', Low:'badge-low',
    Blocked:'badge-blocked',   Mitigated:'badge-mitigated',
    Ongoing:'badge-ongoing',   Resolved:'badge-resolved',
    Yes:'badge-yes',           No:'badge-no',
  }[text] || '';
  return `<span class="badge ${cls}">${text}</span>`;
}

async function loadTable() {
  showSpinner();
  try {
    const filterQ = buildQuery(getFilters());
    const params  = new URLSearchParams();
    params.set('page', currentPage);
    params.set('per_page', 15);
    if (searchTerm) params.set('search', searchTerm);
    if (filterQ) filterQ.split('&').forEach(p => {
      const [k,v] = p.split('=');
      if (k&&v) params.set(k, decodeURIComponent(v));
    });
    const res   = await fetch('/api/incidents?' + params.toString());
    const json  = await res.json();
    const tbody = document.getElementById('table-body');
    if (!json.rows || json.rows.length === 0) {
      tbody.innerHTML = `<tr><td colspan="11" style="text-align:center;color:var(--text-dim);padding:20px">No incidents found.</td></tr>`;
      return;
    }
    const startRow = (json.page - 1) * json.per_page;
    tbody.innerHTML = json.rows.map((r,i) => `
      <tr class="${i%2===0?'row-even':'row-odd'}">
        <td class="row-num">${startRow+i+1}</td>
        <td style="font-family:monospace;color:var(--text-muted);font-size:11px">${r.incident_id}</td>
        <td>${r.date}</td>
        <td>${r.attack_type}</td>
        <td>${r.source_country}</td>
        <td>${r.target_country}</td>
        <td>${r.sector}</td>
        <td style="text-align:center">${r.duration_minutes||'—'}</td>
        <td>${badge(r.data_breach||'—')}</td>
        <td>${badge(r.severity)}</td>
        <td>${badge(r.status)}</td>
      </tr>
    `).join('');
    const totalPages = Math.ceil(json.total / json.per_page);
    document.getElementById('pg-info').textContent =
      `Page ${json.page} of ${totalPages}  (${json.total.toLocaleString()} records)`;
    document.getElementById('pg-prev').disabled = json.page <= 1;
    document.getElementById('pg-next').disabled = json.page >= totalPages;
  } finally {
    hideSpinner();
  }
}

function changePage(dir) { currentPage += dir; loadTable(); }

let searchTimeout;
function searchTable(val) {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => { searchTerm=val.trim(); currentPage=1; loadTable(); }, 350);
}

(async function init() {
  showSpinner();
  try {
    await loadFilterOptions();
    const res  = await fetch('/api/data');
    const data = await res.json();
    renderCharts(data);
    await loadAlerts();
  } finally {
    hideSpinner();
  }
})();