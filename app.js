/* HSO Dragon Migration — dashboard logic */

const state = {
  pipelines: null,   // from data/pipelines.json
  status: null,      // from data/status.json
  view: 'overview',
  sort: { key: 'priority', dir: 'asc' },
  filter: { q: '', prio: 'all', status: 'all' },
  expanded: new Set(),
};

const STATUS_LABELS = {
  done: 'Done',
  dag_done: 'DAG Done',
  blocked: 'Blocked',
  pending: 'Pending',
  testing: 'Testing',
};

const PRIO_ORDER = { P1: 1, P2: 2, P3: 3, P4: 4, P5: 5, unassigned: 99 };

// ---------- boot ----------
document.addEventListener('DOMContentLoaded', init);

async function init() {
  paintClock();
  setInterval(paintClock, 30_000);

  try {
    const [p, s] = await Promise.all([
      fetch('./data/pipelines.json').then(r => { if (!r.ok) throw new Error('pipelines'); return r.json(); }),
      fetch('./data/status.json').then(r => { if (!r.ok) throw new Error('status'); return r.json(); }),
    ]);
    state.pipelines = p;
    state.status = s;
  } catch (e) {
    document.getElementById('viewRoot').innerHTML =
      `<div class="err"><b>Failed to load data.</b><br>
       Expected <span class="mono">./data/pipelines.json</span> and <span class="mono">./data/status.json</span>.<br>
       <span style="color:var(--text-mute);font-size:12px">Detail: ${escapeHtml(e.message || String(e))}</span></div>`;
    return;
  }

  wireNav();
  wireKeys();
  paintSidebarCounts();
  paintFooter();
  paintTopMeta();
  showView('overview');
}

function wireNav() {
  document.querySelectorAll('.nav-item').forEach(el => {
    el.addEventListener('click', () => {
      const v = el.dataset.view;
      document.querySelectorAll('.nav-item').forEach(n => n.classList.toggle('active', n === el));
      showView(v);
    });
  });
}

function wireKeys() {
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closePanel();
  });
  document.getElementById('backdrop').addEventListener('click', closePanel);
}

// ---------- derived helpers ----------
function allNames() { return Object.keys(state.pipelines || {}); }

function pipeRow(name) {
  const p = state.pipelines[name] || {};
  const s = state.status?.[name] || {};
  const total = p.total_tasks ?? (p.tasks ? p.tasks.length : 0);

  // Converted: sum of "Done" from status_counts, else derive from tasks statuses
  let converted = 0;
  if (p.status_counts && typeof p.status_counts === 'object') {
    for (const [k, v] of Object.entries(p.status_counts)) {
      if (/^done$/i.test(k.trim())) converted += Number(v) || 0;
    }
  }
  if (!converted && Array.isArray(p.tasks)) {
    converted = p.tasks.filter(t => /^done$/i.test((t.status || '').trim())) .length;
  }

  const prio = (p.priority || 'unassigned').toString();
  const status = (s.status || 'pending').toLowerCase();
  return {
    name,
    dag_id: p.dag_id || name,
    priority: prio,
    schedule: p.schedule || '—',
    total,
    converted,
    status,
    blocker: s.blocker || '',
    notes: s.notes || '',
    last_updated: s.last_updated || '',
    dag_converted: !!s.dag_converted,
    sql_converted: !!s.sql_converted,
    tested: !!s.tested,
    tasks: p.tasks || [],
    status_counts: p.status_counts || {},
  };
}

function allRows() { return allNames().map(pipeRow); }

function rowsByPrio(prio) {
  if (prio === 'P45') return allRows().filter(r => r.priority === 'P4' || r.priority === 'P5');
  if (prio === 'unassigned') return allRows().filter(r => !['P1','P2','P3','P4','P5'].includes(r.priority));
  return allRows().filter(r => r.priority === prio);
}

function countsByPrio() {
  const rows = allRows();
  return {
    P1: rows.filter(r => r.priority === 'P1').length,
    P2: rows.filter(r => r.priority === 'P2').length,
    P3: rows.filter(r => r.priority === 'P3').length,
    P45: rows.filter(r => r.priority === 'P4' || r.priority === 'P5').length,
    unassigned: rows.filter(r => !['P1','P2','P3','P4','P5'].includes(r.priority)).length,
    all: rows.length,
  };
}

function statusBreakdown(rows = allRows()) {
  const out = { done: 0, dag_done: 0, blocked: 0, pending: 0, testing: 0 };
  rows.forEach(r => { out[r.status] = (out[r.status] || 0) + 1; });
  return out;
}

function totals() {
  const rows = allRows().filter(r => r.name !== 'dragon_L1');
  const totalTasks = rows.reduce((a, r) => a + (r.total || 0), 0);
  const converted = rows.reduce((a, r) => a + (r.converted || 0), 0);
  const blocked = rows.filter(r => r.status === 'blocked').length;
  const done = rows.filter(r => r.status === 'done').length;
  return { totalPipes: rows.length, totalTasks, converted, blocked, done };
}

function l1Totals() {
  const p = state.pipelines?.['dragon_L1'] || {};
  const tasks = p.tasks || [];
  const skipped = tasks.filter(t => /^skip$/i.test((t.status || '').trim())).length;
  return { total: p.total_tasks ?? tasks.length, skipped };
}

// ---------- sidebar ----------
function paintSidebarCounts() {
  const c = countsByPrio();
  const set = (k, v) => {
    const el = document.querySelector(`[data-badge="${k}"]`);
    if (el) el.textContent = v;
  };
  set('P1', c.P1); set('P2', c.P2); set('P3', c.P3);
  set('P45', c.P45); set('unassigned', c.unassigned); set('all', c.all);
}

function paintFooter() {
  const rows = allRows();
  const dates = rows.map(r => r.last_updated).filter(Boolean).sort();
  const last = dates[dates.length - 1];
  document.getElementById('lastUpdated').textContent = last ? 'updated ' + formatDate(last) : 'updated —';
}

function paintTopMeta() {
  const t = totals();
  document.getElementById('projMeta').textContent =
    `${t.totalPipes} pipelines · ${t.totalTasks.toLocaleString()} tasks`;
}

function paintClock() {
  const d = new Date();
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  const el = document.getElementById('nowTime');
  if (el) el.textContent = `${hh}:${mm} WIB`;
}

// ---------- router ----------
function showView(v) {
  state.view = v;
  const root = document.getElementById('viewRoot');
  root.style.opacity = '0';
  root.style.transform = 'translateY(4px)';
  setTimeout(() => {
    root.innerHTML = '';
    if (v === 'overview') renderOverview(root);
    else if (v === 'all') renderAll(root);
    else renderPriorityView(root, v);
    root.style.transition = 'opacity .28s ease, transform .28s ease';
    requestAnimationFrame(() => {
      root.style.opacity = '1';
      root.style.transform = 'translateY(0)';
      // kick post-mount animations
      animateOnMount(root);
    });
    updateCrumbs(v);
  }, 120);
}

function updateCrumbs(v) {
  const map = {
    overview: ['Dashboard', 'Overview'],
    P1: ['Priorities', 'P1 — Critical'],
    P2: ['Priorities', 'P2 — High'],
    P3: ['Priorities', 'P3 — Medium'],
    P45: ['Priorities', 'P4–P5 — Low'],
    unassigned: ['Priorities', 'Unassigned'],
    all: ['Data', 'All Pipelines'],
  };
  const [l, p] = map[v] || map.overview;
  document.getElementById('crumbLevel').textContent = l;
  document.getElementById('crumbPage').textContent = p;
}

// ---------- overview ----------
function renderOverview(root) {
  const t = totals();
  const l1 = l1Totals();
  const b = statusBreakdown(allRows().filter(r => r.name !== 'dragon_L1'));
  const P1_NAMES = [
    'dragon_leads_funnel_management',
    'dragon_customerprofilesales',
    'dragon_partsharecontribution',
    'dragon_ustk2',
    'so2w_dragon_sdue_fabric',
  ];

  const groupProgress = (names) => {
    const rows = names.map(pipeRow);
    const total = rows.reduce((a, r) => a + r.total, 0);
    const conv = rows.reduce((a, r) => a + r.converted, 0);
    return { total, conv, pct: total ? Math.round((conv / total) * 100) : 0, count: rows.length };
  };

  const pGroups = [
    { key: 'p1',  label: 'P1 Critical', names: allRows().filter(r => r.priority === 'P1').map(r => r.name) },
    { key: 'p2',  label: 'P2 High',     names: allRows().filter(r => r.priority === 'P2').map(r => r.name) },
    { key: 'p3',  label: 'P3 Medium',   names: allRows().filter(r => r.priority === 'P3').map(r => r.name) },
    { key: 'p45', label: 'P4–P5 Low',   names: allRows().filter(r => r.priority === 'P4' || r.priority === 'P5').map(r => r.name) },
    { key: 'un',  label: 'Unassigned',  names: allRows().filter(r => !['P1','P2','P3','P4','P5'].includes(r.priority)).map(r => r.name) },
  ].map(g => ({ ...g, ...groupProgress(g.names) }));

  const convPct = t.totalTasks ? Math.round((t.converted / t.totalTasks) * 100) : 0;

  root.innerHTML = `
    <div class="view">
      <h1 class="page-title">Migration Overview</h1>
      <p class="page-sub">Tracking 28 Hadoop/Cloudera pipelines migrating to BigQuery + Cloud Composer.</p>

      <div class="stats">
        ${statCard('Total Pipelines', t.totalPipes, iconLayers(), 'across all priorities', '')}
        ${statCard('Total Tasks', t.totalTasks, iconHash(), 'tasks under tracking', '')}
        ${statCard('Converted', t.converted, iconCheck(), `${convPct}% of total`, 'up')}
        ${statCard('Blocked', t.blocked, iconAlert(), 'needs attention', 'down')}
        ${statCard('L1 Incremental', l1.total, iconClock(), 'deferred — incremental load', '')}
      </div>

      <div class="section">
        <div class="section-head">
          <div class="section-title">Pipeline status</div>
          <div class="section-sub">current phase across ${t.totalPipes} pipelines</div>
        </div>
        <div class="status-grid">
          ${statusRing('Done', b.done || 0, t.totalPipes, 'var(--green)')}
          ${statusRing('DAG Done', b.dag_done || 0, t.totalPipes, 'var(--blue)')}
          ${statusRing('Blocked', b.blocked || 0, t.totalPipes, 'var(--red)')}
          ${statusRing('Pending', (b.pending || 0) + (b.testing || 0), t.totalPipes, 'var(--yellow)')}
        </div>
      </div>

      <div class="section">
        <div class="section-head">
          <div class="section-title">Conversion by priority</div>
          <div class="section-sub">tasks converted per priority group</div>
        </div>
        <div class="card">
          <div class="prog-list">
            ${pGroups.map(g => `
              <div class="prog-row ${g.key === 'p1' ? 'p1' : ''}">
                <div class="prog-name">
                  <span class="chip ${g.key}">${g.label.split(' ')[0]}</span>
                  <span>${g.label.replace(/^P\d\S*\s?/, '').replace(/^P4\S*\s?/, '').trim() || g.label}</span>
                  <span style="color:var(--text-mute);font-size:11.5px">· ${g.count} pipes</span>
                </div>
                <div class="prog-track"><div class="prog-fill" data-pct="${g.pct}" style="width:0%"></div></div>
                <div class="prog-meta"><b>${g.pct}%</b> · ${g.conv}/${g.total}</div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>

      <div class="section">
        <div class="p1-callout">
          <div class="p1-callout-head">
            <div class="p1-callout-title"><span class="p1-dot"></span>P1 Critical — needs attention</div>
            <div class="section-sub">5 pipelines · blocking production cutover</div>
          </div>
          <div class="pipe-grid">
            ${P1_NAMES.map(n => pipeCard(pipeRow(n))).join('')}
          </div>
        </div>
      </div>
    </div>
  `;

  // wire card clicks
  root.querySelectorAll('.pipe-card').forEach(el => {
    el.addEventListener('click', () => openPanel(el.dataset.name));
  });
}

// ---------- priority view ----------
function renderPriorityView(root, prio) {
  const rows = rowsByPrio(prio).sort((a, b) => {
    // blocked first, then by name
    const order = { blocked: 0, pending: 1, testing: 2, dag_done: 3, done: 4 };
    const d = (order[a.status] ?? 9) - (order[b.status] ?? 9);
    if (d) return d;
    return a.name.localeCompare(b.name);
  });

  const prioLabel = {
    P1: 'P1 — Critical', P2: 'P2 — High', P3: 'P3 — Medium',
    P45: 'P4–P5 — Low', unassigned: 'Unassigned',
  }[prio];

  const sub = {
    P1: 'Must-ship pipelines. Currently blocked on source data and dbt models.',
    P2: 'High priority. Scheduled for next conversion wave.',
    P3: 'Medium priority. Scoped but not yet started.',
    P45: 'Low priority. Scheduled after critical cutover.',
    unassigned: 'Pipelines without an assigned priority — includes three high-volume tables.',
  }[prio];

  const totalTasks = rows.reduce((a, r) => a + r.total, 0);
  const conv = rows.reduce((a, r) => a + r.converted, 0);

  root.innerHTML = `
    <div class="view">
      <h1 class="page-title">${prioLabel}</h1>
      <p class="page-sub">${sub}</p>

      <div class="stats" style="grid-template-columns: repeat(4, 1fr)">
        ${statCard('Pipelines', rows.length, iconLayers(), '', '')}
        ${statCard('Tasks', totalTasks, iconHash(), 'under tracking', '')}
        ${statCard('Converted', conv, iconCheck(), totalTasks ? `${Math.round(conv/totalTasks*100)}% of total` : '—', 'up')}
        ${statCard('Blocked', rows.filter(r => r.status === 'blocked').length, iconAlert(), 'awaiting deps', 'down')}
      </div>

      ${rows.length === 0
        ? `<div class="empty"><div class="t">No pipelines in this group</div><div>Nothing to show here yet.</div></div>`
        : `<div class="pipe-grid">${rows.map(pipeCard).join('')}</div>`}
    </div>
  `;

  root.querySelectorAll('.pipe-card').forEach(el => {
    el.addEventListener('click', () => openPanel(el.dataset.name));
  });
}

// ---------- all pipelines table ----------
function renderAll(root) {
  const t = totals();
  root.innerHTML = `
    <div class="view">
      <h1 class="page-title">All Pipelines</h1>
      <p class="page-sub">${t.totalPipes} pipelines · ${t.totalTasks.toLocaleString()} tasks tracked</p>

      <div class="filters">
        <div class="search">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input id="f_q" type="text" placeholder="Search pipelines…" spellcheck="false" autocomplete="off" value="${escapeHtml(state.filter.q)}"/>
        </div>
        <select class="select" id="f_prio">
          <option value="all">All priorities</option>
          <option value="P1">P1 Critical</option>
          <option value="P2">P2 High</option>
          <option value="P3">P3 Medium</option>
          <option value="P4">P4</option>
          <option value="P5">P5</option>
          <option value="unassigned">Unassigned</option>
        </select>
        <select class="select" id="f_status">
          <option value="all">All statuses</option>
          <option value="done">Done</option>
          <option value="dag_done">DAG Done</option>
          <option value="blocked">Blocked</option>
          <option value="pending">Pending</option>
          <option value="testing">Testing</option>
        </select>
      </div>

      <div class="table-wrap">
        <table class="pipes" id="pipeTable">
          <thead>
            <tr>
              ${th('name', 'Pipeline Name')}
              ${th('priority', 'Priority')}
              ${th('total', 'Tasks')}
              ${th('converted', 'Converted')}
              ${th('status', 'Status')}
              ${th('blocker', 'Blocker')}
              ${th('last_updated', 'Last Updated')}
            </tr>
          </thead>
          <tbody id="pipeBody"></tbody>
        </table>
      </div>
    </div>
  `;

  const f_q = root.querySelector('#f_q');
  const f_prio = root.querySelector('#f_prio');
  const f_status = root.querySelector('#f_status');
  f_prio.value = state.filter.prio;
  f_status.value = state.filter.status;
  f_q.addEventListener('input', () => { state.filter.q = f_q.value; paintTableBody(); });
  f_prio.addEventListener('change', () => { state.filter.prio = f_prio.value; paintTableBody(); });
  f_status.addEventListener('change', () => { state.filter.status = f_status.value; paintTableBody(); });
  root.querySelectorAll('thead th').forEach(th => {
    th.addEventListener('click', () => {
      const k = th.dataset.key;
      if (state.sort.key === k) state.sort.dir = state.sort.dir === 'asc' ? 'desc' : 'asc';
      else { state.sort.key = k; state.sort.dir = 'asc'; }
      paintHeadSort();
      paintTableBody();
    });
  });

  paintHeadSort();
  paintTableBody();
}

function th(key, label) {
  return `<th data-key="${key}"><span>${label}</span><span class="sort-ind">▲</span></th>`;
}

function paintHeadSort() {
  document.querySelectorAll('#pipeTable thead th').forEach(el => {
    const k = el.dataset.key;
    el.classList.toggle('sorted', k === state.sort.key);
    const ind = el.querySelector('.sort-ind');
    if (!ind) return;
    ind.textContent = (k === state.sort.key && state.sort.dir === 'desc') ? '▼' : '▲';
  });
}

function paintTableBody() {
  const body = document.getElementById('pipeBody');
  if (!body) return;
  let rows = allRows();
  const { q, prio, status } = state.filter;
  if (q) { const ql = q.toLowerCase(); rows = rows.filter(r => r.name.toLowerCase().includes(ql)); }
  if (prio !== 'all') {
    if (prio === 'unassigned') rows = rows.filter(r => !['P1','P2','P3','P4','P5'].includes(r.priority));
    else rows = rows.filter(r => r.priority === prio);
  }
  if (status !== 'all') rows = rows.filter(r => r.status === status);

  const { key, dir } = state.sort;
  rows.sort((a, b) => {
    let av = a[key], bv = b[key];
    if (key === 'priority') { av = PRIO_ORDER[a.priority] ?? 100; bv = PRIO_ORDER[b.priority] ?? 100; }
    if (key === 'name') { av = a.name; bv = b.name; }
    if (typeof av === 'string' && typeof bv === 'string') {
      return dir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
    }
    av = av ?? 0; bv = bv ?? 0;
    return dir === 'asc' ? av - bv : bv - av;
  });

  if (!rows.length) {
    body.innerHTML = `<tr><td colspan="7"><div class="empty" style="border:none;padding:40px 20px"><div class="t">No matches</div><div>Try clearing your filters.</div></div></td></tr>`;
    return;
  }

  body.innerHTML = rows.map(r => {
    const pct = r.total ? Math.round(r.converted / r.total * 100) : 0;
    const rowHtml = `
      <tr class="row" data-name="${r.name}">
        <td class="pname">${escapeHtml(r.name)}</td>
        <td><span class="prio ${r.priority}">${r.priority}</span></td>
        <td class="tasks-cell">${r.total}</td>
        <td>
          <span class="mini-prog">
            <span class="prog-track"><span class="prog-fill" data-pct="${pct}" style="width:0%"></span></span>
            <span class="meta">${pct}%</span>
          </span>
        </td>
        <td>${badge(r.status)}</td>
        <td class="blocker-cell" title="${escapeHtml(r.blocker)}">${r.blocker ? escapeHtml(r.blocker) : '<span style="color:var(--text-mute)">—</span>'}</td>
        <td class="date-cell">${r.last_updated ? formatDate(r.last_updated) : '—'}</td>
      </tr>
    `;
    const expanded = state.expanded.has(r.name);
    const expandHtml = expanded
      ? `<tr class="expand-row"><td colspan="7"><div class="expand-inner">${taskTable(r)}</div></td></tr>`
      : '';
    return rowHtml + expandHtml;
  }).join('');

  body.querySelectorAll('tr.row').forEach(tr => {
    tr.addEventListener('click', (e) => {
      // Ctrl/meta → inline expand. Plain click → detail panel.
      if (e.metaKey || e.ctrlKey || e.altKey) {
        const n = tr.dataset.name;
        if (state.expanded.has(n)) state.expanded.delete(n); else state.expanded.add(n);
        paintTableBody();
        queueMicrotask(animateProgressBars);
      } else {
        openPanel(tr.dataset.name);
      }
    });
  });

  // animate mini progress bars
  queueMicrotask(animateProgressBars);
}

// ---------- components ----------
function statCard(label, value, icon, foot, trend) {
  return `
    <div class="card stat hoverable">
      <div class="stat-label">${icon} <span>${label}</span></div>
      <div class="stat-value" data-counter="${value}">0</div>
      <div class="stat-foot">
        ${trend ? `<span class="stat-chip ${trend}">${trend === 'up' ? '▲' : '▼'} ${label.toLowerCase()}</span>` : ''}
        <span>${escapeHtml(foot || '')}</span>
      </div>
    </div>
  `;
}

function statusRing(label, count, total, color) {
  const pct = total ? Math.round(count / total * 100) : 0;
  const C = 2 * Math.PI * 18; // r=18
  const off = C * (1 - pct / 100);
  return `
    <div class="card status-cell hoverable">
      <div class="status-ring">
        <svg viewBox="0 0 44 44">
          <circle class="bg" cx="22" cy="22" r="18" fill="none" stroke-width="4"/>
          <circle class="fg" cx="22" cy="22" r="18" fill="none" stroke="${color}" stroke-width="4"
            stroke-linecap="round"
            stroke-dasharray="${C.toFixed(2)}" stroke-dashoffset="${C.toFixed(2)}"
            data-off="${off.toFixed(2)}"/>
        </svg>
        <div class="pct" style="color:${color}">${pct}%</div>
      </div>
      <div>
        <div class="label">${label}</div>
        <div class="count" data-counter="${count}">0</div>
      </div>
    </div>
  `;
}

function pipeCard(r) {
  const pct = r.total ? Math.round(r.converted / r.total * 100) : 0;
  return `
    <div class="card pipe-card hoverable" data-name="${r.name}">
      <div class="row">
        <span class="prio ${r.priority}">${r.priority}</span>
        <span class="pipe-name mono" title="${escapeHtml(r.name)}">${escapeHtml(r.name)}</span>
        ${badge(r.status)}
      </div>
      <div class="pipe-meta mono">
        <span>${iconCal()} ${escapeHtml(r.schedule)}</span>
        <span>${iconTask()} ${r.total} tasks</span>
        <span>${iconClock()} ${r.last_updated ? formatDate(r.last_updated) : '—'}</span>
      </div>
      <div class="pipe-progress">
        <span class="prog-track"><span class="prog-fill" data-pct="${pct}" style="width:0%"></span></span>
        <span class="meta"><b style="color:var(--text)">${pct}%</b> · ${r.converted}/${r.total}</span>
      </div>
      ${r.blocker ? `
        <div class="pipe-blocker">
          ${iconAlert(14)}
          <span>${escapeHtml(r.blocker)}</span>
        </div>
      ` : ''}
    </div>
  `;
}

function badge(status) {
  const label = STATUS_LABELS[status] || status;
  return `<span class="badge ${status}"><span class="dot"></span>${label}</span>`;
}

function taskTable(r) {
  if (!r.tasks.length) return `<div style="color:var(--text-mute);font-size:12px">No task detail available for this pipeline.</div>`;
  return `
    <table class="task-table">
      <thead>
        <tr><th>Task ID</th><th>Type</th><th>Status</th><th>GCP Tool</th><th>Notes</th></tr>
      </thead>
      <tbody>
        ${r.tasks.map(t => `
          <tr>
            <td class="tid">${escapeHtml(t.task_id || '')}</td>
            <td style="color:var(--text-dim)">${escapeHtml(t.type || '—')}</td>
            <td>${taskStatus(t.status)}</td>
            <td style="color:var(--text-dim)">${escapeHtml(t.tool || '—')}</td>
            <td style="color:var(--text-mute);max-width:280px">${escapeHtml(t.catatan || t.notes || '')}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

function taskStatus(s) {
  const raw = (s || '').trim();
  const key = raw.replace(/\s+/g, '');
  const cls = /^skip$/i.test(raw) ? 'SKIP'
            : /^belumconvert$/i.test(key) ? 'BelumConvert'
            : /^done$/i.test(raw) ? 'Done'
            : /^needinput$/i.test(key) ? 'NEEDINPUT'
            : 'SKIP';
  return `<span class="st ${cls}">${escapeHtml(raw || '—')}</span>`;
}

// ---------- detail panel ----------
function openPanel(name) {
  const r = pipeRow(name);
  const panel = document.getElementById('panel');
  const back = document.getElementById('backdrop');

  const counts = r.status_counts || {};
  const done = Number(counts['Done'] || 0);
  const belum = Number(counts['Belum Convert'] || 0);
  const skip = Number(counts['SKIP'] || 0);
  const need = Number(counts['NEED INPUT'] || 0);

  panel.innerHTML = `
    <div class="panel-head">
      <div style="flex:1;min-width:0">
        <h2>${escapeHtml(r.dag_id)}</h2>
        <div class="meta-row">
          <span class="prio ${r.priority}">${r.priority}</span>
          ${badge(r.status)}
          <span style="color:var(--text-mute)">·</span>
          <span>${escapeHtml(r.schedule)}</span>
          <span style="color:var(--text-mute)">·</span>
          <span>${r.last_updated ? formatDate(r.last_updated) : 'not updated'}</span>
        </div>
      </div>
      <button class="panel-close" aria-label="Close" id="panelClose">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>
    <div class="panel-body">
      ${r.blocker ? `
        <div class="alert-blocker">
          ${iconAlert(16)}
          <div>
            <div class="t">Blocker</div>
            <div class="b">${escapeHtml(r.blocker)}</div>
          </div>
        </div>
      ` : ''}

      ${r.notes ? `
        <div class="notes-box">
          <div class="t">Notes</div>
          <div class="b">${escapeHtml(r.notes)}</div>
        </div>
      ` : ''}

      <div class="panel-stats">
        <div class="cell"><div class="l">Total tasks</div><div class="v">${r.total}</div></div>
        <div class="cell"><div class="l">Done</div><div class="v" style="color:var(--green)">${done || r.converted}</div></div>
        <div class="cell"><div class="l">Belum Convert</div><div class="v" style="color:var(--yellow)">${belum}</div></div>
        <div class="cell"><div class="l">Skip / Need Input</div><div class="v" style="color:var(--text-dim)">${skip + need}</div></div>
      </div>

      <div style="display:flex;gap:14px;margin-bottom:18px;font-size:12px;flex-wrap:wrap">
        ${flagPill('DAG Converted', r.dag_converted)}
        ${flagPill('SQL Converted', r.sql_converted)}
        ${flagPill('Tested', r.tested)}
      </div>

      <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.07em;color:var(--text-mute);font-weight:600;margin-bottom:10px">Task Breakdown</div>
      <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;overflow:hidden">
        ${taskTable(r)}
      </div>
    </div>
  `;

  panel.classList.add('open');
  panel.setAttribute('aria-hidden', 'false');
  back.classList.add('open');
  panel.querySelector('#panelClose').addEventListener('click', closePanel);
}

function flagPill(label, ok) {
  return `
    <span style="display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border-radius:6px;
      background:${ok ? 'rgba(0,208,132,0.07)' : '#161616'};
      border:1px solid ${ok ? 'rgba(0,208,132,0.22)' : 'var(--border)'};
      color:${ok ? 'var(--green)' : 'var(--text-mute)'};font-size:12px;font-weight:500">
      ${ok
        ? `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`
        : `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/></svg>`}
      ${label}
    </span>
  `;
}

function closePanel() {
  const panel = document.getElementById('panel');
  const back = document.getElementById('backdrop');
  panel.classList.remove('open');
  panel.setAttribute('aria-hidden', 'true');
  back.classList.remove('open');
}

// ---------- mount animations ----------
function animateOnMount(root) {
  // counters
  root.querySelectorAll('[data-counter]').forEach(el => {
    const target = Number(el.getAttribute('data-counter')) || 0;
    animateCounter(el, target, 900);
  });
  animateProgressBars(root);
  // status ring dashoffsets
  root.querySelectorAll('.status-ring .fg').forEach(el => {
    requestAnimationFrame(() => {
      el.style.strokeDashoffset = el.getAttribute('data-off');
    });
  });
}

function animateProgressBars(scope) {
  const root = scope instanceof Element ? scope : document;
  root.querySelectorAll('.prog-fill').forEach(el => {
    const pct = Number(el.getAttribute('data-pct')) || 0;
    // slight stagger
    setTimeout(() => { el.style.width = pct + '%'; }, 40);
  });
}

function animateCounter(el, target, duration) {
  const start = performance.now();
  const from = 0;
  const ease = t => 1 - Math.pow(1 - t, 3);
  function tick(now) {
    const t = Math.min(1, (now - start) / duration);
    const v = Math.round(from + (target - from) * ease(t));
    el.textContent = v.toLocaleString();
    if (t < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

// ---------- icons ----------
function svg(d, size = 13) {
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${d}</svg>`;
}
const iconLayers = () => svg('<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>');
const iconHash = () => svg('<line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/>');
const iconCheck = () => svg('<polyline points="20 6 9 17 4 12"/>');
const iconAlert = (s = 13) => svg('<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12" y2="17"/>', s);
const iconCal = () => svg('<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>');
const iconTask = () => svg('<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 12l2 2 4-4"/>');
const iconClock = () => svg('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>');

// ---------- utils ----------
function formatDate(d) {
  const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(d);
  if (!m) return d;
  const day = parseInt(m[3], 10);
  const mo = MONTHS[parseInt(m[2], 10) - 1];
  return `${day} ${mo} ${m[1]}`;
}

function escapeHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
