let currentTab = 'today';
let companyDrill = false;      // true while viewing a single company's contacts
let _companies = [], _prospects = [], _campaigns = [];
let _signals = null;           // last /api/signals payload, for the cohort builder
let _desk = { items: [], i: 0 };

// ── Appearance ──
//
// Three states, not two: "auto" follows the OS and is the default, so the
// dashboard matches the rest of your machine until you deliberately override
// it. Stored per-browser; nothing is sent anywhere.

const THEMES = ['auto', 'light', 'dark'];

function applyTheme(mode) {
  const root = document.documentElement;
  if (mode === 'auto') root.removeAttribute('data-theme');
  else root.setAttribute('data-theme', mode);
  const btn = document.getElementById('theme-btn');
  if (btn) btn.textContent = mode;
}

function cycleTheme() {
  const now = localStorage.getItem('harvey-theme') || 'auto';
  const next = THEMES[(THEMES.indexOf(now) + 1) % THEMES.length];
  try { localStorage.setItem('harvey-theme', next); } catch { /* private mode */ }
  applyTheme(next);
}

(function initTheme() {
  let saved = 'auto';
  try { saved = localStorage.getItem('harvey-theme') || 'auto'; } catch { /* ignore */ }
  applyTheme(THEMES.includes(saved) ? saved : 'auto');
})();

// ── Utilities ──

function escHtml(s) {
  if (s === null || s === undefined || s === '') return '';
  return String(s).replace(/[&<>"']/g, ch => (
    {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]
  ));
}

// ── One status vocabulary ──
//
// Mariana's tables each carry their own words for state: a prospect is `new`,
// a campaign is `draft`, an email is `pending_review`, a signal is `proposed`.
// Five of those mean "waiting on you" and the old dashboard styled every one
// differently. Everything now resolves through this map, so a status reads the
// same way no matter which table it came out of.
//
// tone: waiting (needs a human) | active (in flight) | good | bad | idle
const STATUS = {
  // prospects
  new:            ['Novo', 'active'],
  contacted:      ['Contatado', 'active'],
  replied:        ['Respondeu', 'good'],
  interested:     ['Interessado', 'good'],
  meeting:        ['Call marcada', 'note'],
  not_interested: ['Sem interesse', 'bad'],
  bounced:        ['Voltou (bounce)', 'bad'],
  // campaigns
  draft:          ['Rascunho', 'waiting'],
  active:         ['Ativa', 'good'],
  completed:      ['Concluída', 'idle'],
  paused:         ['Pausada', 'bad'],
  // conversations
  open:           ['Aberta', 'active'],
  closed:         ['Encerrada', 'idle'],
  closed_won:     ['Ganho', 'good'],
  closed_lost:    ['Perdido', 'bad'],
  objection:      ['Objeção', 'waiting'],
  // outbox
  pending_review: ['Esperando você', 'waiting'],
  approved:       ['Aprovado', 'good'],
  scheduled:      ['Agendado', 'active'],
  sent:           ['Enviado', 'good'],
  failed:         ['Falhou', 'bad'],
  rejected:       ['Recusado', 'idle'],
  cancelled:      ['Cancelado', 'idle'],
  // signals
  proposed:       ['Esperando você', 'waiting'],
  confirmed:      ['Confirmado', 'good'],
  // email deliverability
  verified:       ['Verificado', 'good'],
  risky:          ['Aceita tudo', 'waiting'],
  guess:          ['Não verificado', 'idle'],
  invalid:        ['Inválido', 'bad'],
  // runs
  running:        ['Rodando', 'active'],
  stale:          ['Travado', 'bad'],
  // Mariana
  queued:         ['Na fila', 'active'],
  opted_out:      ['Pediu para sair', 'bad'],
  lost:           ['Perdido', 'bad'],
  needs_human:    ['Precisa de você', 'waiting'],
  question:       ['Pergunta', 'waiting'],
  wrong_person:   ['Pessoa errada', 'idle'],
  ooo:            ['Ausente', 'idle'],
  unsubscribe:    ['Pediu para sair', 'bad'],
  escalate:       ['Precisa de você', 'waiting'],
};

function statusMeta(status) {
  const key = String(status || '').toLowerCase().replace(/[^a-z0-9]+/g, '_');
  const hit = STATUS[key];
  if (hit) return { label: hit[0], tone: hit[1] };
  const label = String(status || 'desconhecido').replace(/_/g, ' ');
  return { label: label.charAt(0).toUpperCase() + label.slice(1), tone: 'idle' };
}

function badge(status) {
  const m = statusMeta(status);
  return '<span class="badge t-' + m.tone + '">' + escHtml(m.label) + '</span>';
}

function formatDate(d) {
  if (!d) return '';
  try {
    const dt = new Date(d);
    if (isNaN(dt)) return escHtml(d);
    return dt.toLocaleString('pt-BR', {month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});
  } catch { return escHtml(d); }
}

function emptyState(glyph, title, copy) {
  return '<div class="empty"><div class="glyph">' + glyph + '</div>' +
    '<div class="title">' + title + '</div>' +
    '<div class="copy">' + copy + '</div></div>';
}

function offlineState() {
  return emptyState('&#9888;', 'O painel não está achando o servidor',
    'O processo do painel pode ter parado. Rode <b>mariana dashboard</b> de novo e atualize esta página.');
}

async function api(path, opts) {
  try {
    const r = await fetch(path, opts);
    if (!r.ok) return null;
    return await r.json();
  } catch {
    return null;
  }
}

function showToast(msg, type) {
  const t = document.createElement('div');
  t.className = 'toast ' + type;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2600);
}

function toggleVisibility(inputId) {
  const el = document.getElementById(inputId);
  el.type = el.type === 'password' ? 'text' : 'password';
}

// ── Tabs ──

function showTab(id, btn) {
  currentTab = id;
  if (id === 'companies') companyDrill = false;
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  if (btn) btn.classList.add('active');
  loadCurrentTab();
}

function loadCurrentTab() {
  switch (currentTab) {
    case 'today': loadToday(); loadSetupStatus(); loadRuns(); loadTodayActivity(); break;
    case 'signals': loadSignals(); break;
    case 'discover': loadDiscoverProviders(); break;
    case 'companies': if (!companyDrill) loadCompanies(); break;
    case 'prospects': loadProspects(); break;
    case 'campaigns': loadCampaigns(); break;
    case 'outbox': loadOutbox(); break;
    case 'channels': loadChannels(); break;
    case 'jobs': loadJobs(); break;
    case 'metrics': loadMetrics(); break;
    case 'conversations': loadConversations(); break;
    case 'activity': loadActivity(); break;
    case 'usage': loadUsage(); break;
    case 'settings': loadSettings(); break;
    case 'controls': loadMarianaStatus(); loadLogs(); break;
  }
}

// ── Today: what needs a human ──

async function loadToday() {
  const data = await api('/api/today');
  const el = document.getElementById('today-queue');
  if (!data) { el.innerHTML = offlineState(); return; }

  navCount('nav-today', (data.items || []).filter(i => i.tone !== 'good').length);
  navCount('nav-outbox', (data.stats || {}).outbox_pending || 0);
  renderFigures(data.stats || {});

  const items = data.items || [];
  if (!items.length) {
    el.innerHTML = '<div class="queue-clear">' +
      '<div class="glyph">&#10003;</div><div>' +
      '<div class="qtitle">Nada esperando por você</div>' +
      '<div class="qdetail">A Mariana tem tudo de que precisa. O que exigir uma ' +
      'decisão (um email para aprovar, um sinal para confirmar) aparece aqui.</div>' +
      '</div></div>';
    return;
  }

  el.innerHTML = '<div class="queue">' + items.map(it =>
    '<div class="queue-item ' + escHtml(it.tone || 'warn') + '">' +
      '<div class="qtext">' +
        '<div class="qtitle">' + escHtml(it.title) + '</div>' +
        '<div class="qdetail">' + escHtml(it.detail) + '</div>' +
      '</div>' +
      '<button class="btn btn-secondary btn-sm" onclick="goTab(\'' + escHtml(it.tab) + '\')">' +
        escHtml(it.action) + '</button>' +
    '</div>'
  ).join('') + '</div>';
}

function renderFigures(stats) {
  const el = document.getElementById('today-figures');
  if (!el) return;
  const row = (label, value) =>
    '<div class="figure"><span class="k">' + label + '</span>' +
    '<span class="v' + (value ? '' : ' zero') + '">' + value + '</span></div>';

  el.innerHTML = '<div class="figures">' +
    row('Empresas', stats.companies || 0) +
    row('Contatos', stats.prospects || 0) +
    row('Sinais ligados', stats.signals_confirmed || 0) +
    row('Sites a ler', stats.unprofiled || 0) +
    row('Esperando aprovação', stats.outbox_pending || 0) +
    row('Agendados', stats.outbox_approved || 0) +
    row('Conversas abertas', stats.open_conversations || 0) +
  '</div>';
}

async function loadTodayActivity() {
  const el = document.getElementById('today-activity');
  if (!el) return;
  const data = await api('/api/activity');
  if (!Array.isArray(data) || !data.length) {
    el.innerHTML = '<p class="muted" style="font-size:12.5px">' +
      'Nada ainda. Toda ação da Mariana aparece aqui.</p>';
    return;
  }
  el.innerHTML = '<div class="activity-feed">' + data.slice(0, 12).map(a =>
    '<div class="activity-item">' +
      '<span class="time">' + formatDate(a.created_at) + '</span>' +
      '<span class="agent">' + escHtml(a.agent) + '</span>' +
      '<span class="action">' + escHtml(String(a.action_type).replace(/_/g, ' ')) + '</span>' +
    '</div>').join('') + '</div>';
}

function navCount(id, n) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = n > 0 ? n : '';
  el.className = 'nav-count' + (n > 0 ? ' on' : '');
}

// Jump to a tab from a link that isn't itself a nav button.
function goTab(id) {
  const btns = [...document.querySelectorAll('nav button')];
  const btn = btns.find(b => (b.getAttribute('onclick') || '').includes("'" + id + "'"));
  showTab(id, btn);
}

async function loadRuns() {
  const el = document.getElementById('today-runs');
  const block = document.getElementById('today-runs-block');
  if (!el) return;
  const runs = await api('/api/runs');
  if (!Array.isArray(runs) || !runs.length) {
    if (block) block.style.display = 'none';
    el.innerHTML = '';
    return;
  }
  if (block) block.style.display = '';

  // A rail is 300px wide — a seven-column table does not belong here.
  el.innerHTML = '<div class="figures">' + runs.slice(0, 6).map(r =>
    '<div class="figure" style="align-items:flex-start">' +
      '<span class="k">' + escHtml(r.stage) +
        '<br><span class="muted" style="font-size:11px">' +
        formatDate(r.started_at) + '</span></span>' +
      '<span style="text-align:right;flex:none">' + badge(r.status) +
        '<br><span class="muted" style="font-family:var(--mono);font-size:11px">' +
        (r.records || 0) + ' registros &middot; ' +
        (r.cost_usd ? '$' + Number(r.cost_usd).toFixed(4) : 'grátis') + '</span></span>' +
    '</div>').join('') + '</div>';
}

// ── Setup checklist (lives on Today, and disappears once it's done) ──

async function loadSetupStatus() {
  const el = document.getElementById('today-setup');
  if (!el) return;
  const data = await api('/api/setup-status');
  if (!data || !data.checks) { el.innerHTML = ''; return; }

  const pct = data.percent || 0;
  // Finished setup disappears completely rather than greeting you forever.
  if (pct === 100) { el.innerHTML = ''; return; }

  const renderCheck = (c, optional) =>
    '<div class="check-item">' +
      (c.done ? '<span class="check-icon done">&#10003;</span>'
              : '<span class="check-icon pending"></span>') +
      '<div class="check-info">' +
        '<div class="check-label ' + (c.done ? 'done' : '') + '">' + escHtml(c.label) +
          (optional ? '<span class="optional-tag">opcional</span>' : '') + '</div>' +
        (!c.done ? '<div class="check-help">' + escHtml(c.help) + '</div>' : '') +
      '</div></div>';

  const required = data.checks.filter(c => c.required);
  const optional = data.checks.filter(c => !c.required);

  el.innerHTML =
    '<div class="rail-block">' +
      '<div class="subhead">Configuração &mdash; ' + pct + '%</div>' +
      '<div class="progress-bar" style="margin-bottom:14px">' +
        '<div class="progress-fill yellow" style="width:' + pct + '%"></div></div>' +
      required.map(c => renderCheck(c, false)).join('') +
      (optional.length
        ? '<details style="margin-top:10px"><summary class="muted" ' +
          'style="font-size:12px">' + optional.length + ' opcionais</summary>' +
          '<div style="margin-top:6px">' +
          optional.map(c => renderCheck(c, true)).join('') + '</div></details>'
        : '') +
    '</div>';
}

// ── Signals: Mariana proposes, you confirm ──

async function loadSignals() {
  const data = await api('/api/signals');
  const sumEl = document.getElementById('signals-summary');
  const grpEl = document.getElementById('signals-groups');
  if (!data || data.error) { grpEl.innerHTML = offlineState(); sumEl.innerHTML = ''; return; }
  _signals = data;

  const s = data.summary || {};
  navCount('nav-signals', s.proposed || 0);
  sumEl.innerHTML = '<div class="sig-summary">' +
    ['confirmed', 'proposed', 'rejected'].map(k =>
      '<div class="sig-stat ' + k + '"><div class="n">' + (s[k] || 0) + '</div>' +
      '<div class="k">' + ({proposed: 'esperando você', confirmed: 'confirmados', rejected: 'recusados'}[k] || k) + '</div></div>'
    ).join('') +
    '</div>';

  grpEl.innerHTML = (data.groups || []).map(g => {
    const codes = g.signals.map(x => x.code);
    const undecided = g.signals.filter(x => x.status === 'proposed').length;
    return '<div class="sig-group">' +
      '<div class="sig-group-head"><div>' +
        '<h3>' + escHtml(g.label) + '</h3><p>' + escHtml(g.blurb) + '</p>' +
      '</div>' +
      (undecided
        ? '<div style="display:flex;gap:6px;flex-shrink:0">' +
            '<button class="btn btn-primary btn-sm" onclick=\'setSignals(' +
              JSON.stringify(codes) + ", \"confirmed\")'>Confirmar todos " + undecided + '</button>' +
            '<button class="btn btn-secondary btn-sm" onclick=\'setSignals(' +
              JSON.stringify(codes) + ", \"rejected\")'>Pular todos</button>" +
          '</div>'
        : '') +
      '</div>' +
      '<div class="card" style="padding:4px 0">' + g.signals.map(sigRow).join('') + '</div>' +
    '</div>';
  }).join('');

  renderCohortBuilder();
}

function sigRow(sig) {
  const free = /free|included|grátis|incluído/i.test(sig.cost_note || '');
  const costCls = free ? 'free' : (/\$/.test(sig.cost_note || '') ? 'paid' : '');
  const seen = sig.companies
    ? '<span class="cost-chip">visto em ' + sig.companies +
      (sig.companies === 1 ? ' empresa' : ' empresas') + ' até agora</span>' : '';
  const floor = sig.confidence_floor > 0
    ? '<span class="cost-chip">só registrado acima de ' +
      Math.round(sig.confidence_floor * 100) + '% de confiança</span>' : '';

  const decide = sig.status === 'confirmed'
    ? '<button class="btn btn-secondary btn-sm" onclick="setSignals([\'' + sig.code +
        '\'],\'rejected\')">Desligar</button>'
    : sig.status === 'rejected'
      ? '<button class="btn btn-secondary btn-sm" onclick="setSignals([\'' + sig.code +
          '\'],\'confirmed\')">Ligar</button>'
      : '<button class="btn btn-primary btn-sm" onclick="setSignals([\'' + sig.code +
          '\'],\'confirmed\')">Confirmar</button>' +
        '<button class="btn btn-secondary btn-sm" onclick="setSignals([\'' + sig.code +
          '\'],\'rejected\')">Pular</button>';

  return '<div class="sig-row ' + (sig.status === 'rejected' ? 'rejected' : '') + '">' +
    '<div class="sig-main">' +
      '<div class="sig-label">' + escHtml(sig.label || sig.code) +
        '<span class="sig-code">' + escHtml(sig.code) + '</span></div>' +
      '<div class="sig-desc">' + escHtml(sig.description) + '</div>' +
      '<div class="sig-meta">' +
        '<span class="cost-chip ' + costCls + '">' + escHtml(sig.cost_note || 'custo desconhecido') + '</span>' +
        floor + seen + badge(sig.status) +
      '</div>' +
    '</div>' +
    '<div class="sig-decide">' + decide + '</div>' +
  '</div>';
}

async function setSignals(codes, status) {
  const data = await api('/api/signals/status', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({codes: codes, status: status}),
  });
  if (data && data.success) {
    showToast(
      status === 'confirmed'
        ? data.changed + (data.changed === 1 ? ' sinal confirmado' : ' sinais confirmados') +
          '. A Mariana passa a coletar a partir de agora.'
        : data.changed + (data.changed === 1 ? ' sinal desligado.' : ' sinais desligados.'),
      'success');
  } else {
    showToast('Não deu para atualizar esse sinal.', 'error');
  }
  loadSignals();
}

// ── Discover: pick a source, price it, then run it ──

let _provider = null;
let _discoverPoll = null;

async function loadDiscoverProviders() {
  const el = document.getElementById('discover-providers');
  const data = await api('/api/discover/providers');
  if (!data || !data.providers) { el.innerHTML = offlineState(); return; }

  _provider = _provider || data.selected || data.default;
  el.innerHTML = '<div class="prov-grid">' + data.providers.map(p => {
    const ready = p.configured
      ? '<span class="badge t-good">pronto</span>'
      : '<span class="badge t-waiting">precisa de chave</span>';
    return '<div class="prov-card ' + (p.key === _provider ? 'selected' : '') +
      '" onclick="pickProvider(\'' + p.key + '\')">' +
      '<div class="prov-head"><h3>' + escHtml(p.label) + '</h3>' + ready + '</div>' +
      '<div class="blurb">' + escHtml(p.blurb) + '</div>' +
      '<div class="row"><span class="k">Custo</span><span class="v">' +
        escHtml(p.cost_note) + '</span></div>' +
      '<div class="row"><span class="k">Grátis</span><span class="v">' +
        escHtml(p.free_tier) + '</span></div>' +
      (p.needs_key
        ? '<div class="row"><span class="k">Configurar</span><span class="v">' +
          escHtml(p.env_keys.join(', ')) + ' no .env &middot; ' +
          '<a href="' + escHtml(p.signup_url) + '" target="_blank" rel="noopener">pegar a chave</a>' +
          '</span></div>'
        : '') +
      (p.caveat ? '<div class="caveat">' + escHtml(p.caveat) + '</div>' : '') +
    '</div>';
  }).join('') + '</div>';

  const running = data.running;
  document.getElementById('disc-stop').style.display = running ? '' : 'none';
  if (running && !_discoverPoll) {
    _discoverPoll = setInterval(loadDiscoverProviders, 4000);
  } else if (!running && _discoverPoll) {
    clearInterval(_discoverPoll);
    _discoverPoll = null;
    // A finished run leaves the button stuck on "Running…" otherwise.
    const btn = document.getElementById('disc-run');
    btn.disabled = true;
    btn.textContent = 'Estime primeiro';
    showToast('Busca concluída.', 'success');
  }
  renderDiscoverResult(data.last_report, running);
}

function pickProvider(key) {
  _provider = key;
  document.getElementById('disc-run').disabled = true;
  document.getElementById('disc-run').textContent = 'Estime primeiro';
  document.getElementById('discover-estimate').innerHTML = '';
  loadDiscoverProviders();
}

function discoverBody() {
  const raw = document.getElementById('disc-cities').value.trim();
  return {
    provider: _provider,
    // Semicolons or newlines, never commas: "Denver, CO" is one city.
    cities: raw ? raw.split(/[;\n]/).map(c => c.trim()).filter(Boolean) : [],
    depth: Number(document.getElementById('disc-depth').value) || 30,
    limit: Number(document.getElementById('disc-limit').value) || 100,
    max_spend: Number(document.getElementById('disc-cap').value) || 1,
  };
}

async function estimateDiscovery() {
  const el = document.getElementById('discover-estimate');
  el.innerHTML = '<p class="muted" style="font-size:13px">Calculando o custo…</p>';
  const data = await api('/api/discover/estimate', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(discoverBody()),
  });
  if (!data || data.error) {
    el.innerHTML = '<div class="test-result error">' +
      escHtml((data && data.error) || 'Não deu para estimar.') + '</div>';
    return;
  }

  const cap = discoverBody().max_spend;
  const over = data.estimated_cost > cap;
  el.innerHTML = '<div class="estimate-box">' +
    '<div class="amount ' + (data.free ? 'free' : 'paid') + '">' +
      (data.free ? 'Grátis' : 'US$ ' + data.estimated_cost.toFixed(4)) + '</div>' +
    '<div class="muted" style="font-size:13px;margin-top:2px">' +
      data.query_count + (data.query_count === 1 ? ' busca' : ' buscas') +
      (data.free ? '' : ' &middot; teto de US$ ' + cap.toFixed(2)) + '</div>' +
    (over ? '<div class="test-result error" style="margin-top:12px">' +
      'Passou do teto. Aumente o teto ou diminua a busca.</div>' : '') +
    '<div class="query-list">' +
      data.queries.slice(0, 40).map(escHtml).join('<br>') +
      (data.queries.length > 40 ? '<br>… e mais ' + (data.queries.length - 40) : '') +
    '</div></div>';

  const btn = document.getElementById('disc-run');
  btn.disabled = over;
  btn.textContent = over ? 'Passou do teto'
    : (data.free ? 'Rodar (grátis)' : 'Rodar (gasto até US$ ' + data.estimated_cost.toFixed(2) + ')');
}

async function runDiscovery() {
  const btn = document.getElementById('disc-run');
  btn.disabled = true;
  btn.textContent = 'Rodando…';
  const data = await api('/api/discover/run', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(discoverBody()),
  });
  if (data && data.success) {
    showToast('Busca iniciada: ' + data.queries + ' buscas.', 'success');
  } else {
    showToast((data && data.message) || 'Não deu para iniciar.', 'error');
    btn.disabled = false;
  }
  loadDiscoverProviders();
}

async function stopDiscovery() {
  const data = await api('/api/discover/stop', {method: 'POST'});
  showToast(data && data.success ? 'Parando depois da busca atual.'
                                 : 'Não deu para parar.', data ? 'success' : 'error');
  loadDiscoverProviders();
}

function renderDiscoverResult(report, running) {
  const el = document.getElementById('discover-result');
  if (running) {
    el.innerHTML = '<div class="card"><h2>Rodando…</h2>' +
      '<p class="muted" style="font-size:13px">A Mariana está fazendo as ' +
      'buscas. Os resultados vão para Empresas, e o registro fica em Hoje.</p></div>';
    return;
  }
  if (!report) { el.innerHTML = ''; return; }

  const stat = (label, value, tone) =>
    '<div class="stat-card"><div class="label">' + label + '</div>' +
    '<div class="value"' + (tone ? ' style="color:var(--' + tone + ')"' : '') + '>' +
    value + '</div></div>';

  el.innerHTML = '<div class="subhead">Última busca</div>' +
    '<div class="stats-grid">' +
      stat('Empresas novas', report.new_companies || 0, 'accent') +
      stat('Já conhecidas', report.known_companies || 0) +
      stat('Observações', report.observations || 0) +
      stat('Descartadas (lixo)', report.junk || 0) +
      stat('Custo real', report.actual_cost ? 'US$ ' + report.actual_cost.toFixed(4) : 'grátis') +
    '</div>' +
    (report.stopped ? '<div class="test-result error" style="margin-top:14px">' +
      'Parou antes: ' + escHtml(report.stopped) + '</div>' : '') +
    ((report.errors || []).length
      ? '<div class="card" style="margin-top:14px"><h2>Problemas</h2>' +
        (report.errors || []).slice(0, 8).map(e =>
          '<div class="check-help">' + escHtml(e) + '</div>').join('') + '</div>'
      : '');
}

// ── Cohort builder: a prospect list is a query ──

let _cohort = { require: new Set(), exclude: new Set() };

function renderCohortBuilder() {
  const el = document.getElementById('cohort-builder');
  if (!el || !_signals) return;

  const confirmed = (_signals.groups || [])
    .flatMap(g => g.signals)
    .filter(s => s.status === 'confirmed');

  if (!confirmed.length) {
    el.innerHTML = '<p class="muted" style="font-size:13px">' +
      'Confirme alguns sinais acima e eles viram as peças daqui.</p>';
    document.getElementById('cohort-result').innerHTML = '';
    return;
  }

  const col = (title, key, hint) =>
    '<div><div class="subhead" style="margin-top:0">' + title +
      ' <span class="muted" style="font-weight:400;text-transform:none;letter-spacing:0">' +
      hint + '</span></div><div class="cohort-grid">' +
    confirmed.map(s =>
      '<label class="cohort-pick"><input type="checkbox" ' +
        (_cohort[key].has(s.code) ? 'checked ' : '') +
        'onchange="toggleCohort(\'' + key + '\',\'' + s.code + '\',this.checked)">' +
        '<span>' + escHtml(s.label || s.code) + '</span>' +
        '<span class="n">' + (s.companies || 0) + '</span></label>'
    ).join('') + '</div></div>';

  el.innerHTML = col('Precisa ter', 'require', '&mdash; toda empresa do público tem todos estes') +
    '<div style="height:18px"></div>' +
    col('Não pode ter', 'exclude', '&mdash; desqualificam');
}

function toggleCohort(key, code, on) {
  if (on) _cohort[key].add(code); else _cohort[key].delete(code);
  // A company can't be both required and excluded on the same signal.
  const other = key === 'require' ? 'exclude' : 'require';
  if (on) _cohort[other].delete(code);
  runCohort();
  renderCohortBuilder();
}

async function runCohort() {
  const el = document.getElementById('cohort-result');
  if (!el) return;
  const require = [..._cohort.require], exclude = [..._cohort.exclude];
  if (!require.length) { el.innerHTML = ''; return; }

  const data = await api('/api/cohort', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({require: require, exclude: exclude}),
  });
  if (!data) { el.innerHTML = ''; return; }

  let html = '<div style="border-top:1px solid var(--border);margin-top:20px;padding-top:20px">' +
    '<div class="cohort-size">' + data.size + '</div>' +
    '<div class="muted" style="font-size:13px;margin-top:2px">' +
      (data.size === 1 ? 'empresa bate' : 'empresas batem') + ' com este público agora</div>';

  if (data.companies && data.companies.length) {
    html += '<div class="table-card" style="margin-top:16px"><table><thead><tr>' +
      '<th>Empresa</th><th>Domínio</th><th>Segmento</th><th>Local</th>' +
      '</tr></thead><tbody>' +
      data.companies.slice(0, 50).map(c =>
        '<tr><td>' + escHtml(c.name) + '</td><td class="muted">' + escHtml(c.domain) + '</td>' +
        '<td class="muted">' + escHtml(c.industry) + '</td>' +
        '<td class="muted">' + escHtml(c.location) + '</td></tr>'
      ).join('') + '</tbody></table></div>';
    if (data.size > 50) {
      html += '<p class="muted" style="font-size:12px;margin-top:10px">Mostrando as primeiras 50.</p>';
    }
  } else if (data.size === 0) {
    html += '<p class="muted" style="font-size:13px;margin-top:12px">' +
      'Nenhuma empresa tem todos esses ainda. Afrouxe o público ou rode ' +
      'a prospecção para coletar mais.</p>';
  }
  el.innerHTML = html + '</div>';
}

// ── Settings ──

async function loadSettings() {
  const data = await api('/api/settings');
  if (!data) return;

  // Active provider indicator
  const prov = data.provider || 'instantly';
  const provEl = document.getElementById('active-provider');
  if (provEl) provEl.textContent = prov;

  // Secret fields never echo a value — show a "saved" placeholder instead.
  const savedPh = (id, isSet, base) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.value = '';
    el.placeholder = isSet ? 'Salvo. Digite um valor novo para trocar' : base;
  };
  const tag = (id, ok, okLabel) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.className = 'email-tag ' + (ok ? 'verified' : 'guess');
    el.textContent = ok ? okLabel : 'não configurado';
  };

  // Non-secret values repopulate
  document.getElementById('gmail-id').value = data.gmail_client_id || '';
  document.getElementById('smtp-host').value = data.smtp_host || '';
  document.getElementById('smtp-port').value = data.smtp_port || '';
  document.getElementById('smtp-user').value = data.smtp_username || '';
  document.getElementById('cf-account-id').value = data.cloudflare_account_id || '';

  savedPh('gmail-secret', data.gmail_client_secret_set, 'Cole o segredo do cliente');
  savedPh('smtp-pass', data.smtp_password_set, 'Senha ou senha de app');
  savedPh('instantly-key', data.instantly_api_key_set, 'Cole a chave da API do Instantly');
  savedPh('reoon-key', data.reoon_api_key_set, '600 grátis/mês: reoon.com/email-verifier');
  savedPh('zerobounce-key', data.zerobounce_api_key_set, '100 grátis/mês: o melhor para Microsoft 365/Workspace');
  savedPh('hunter-key', data.hunter_api_key_set, '50 grátis/mês + padrão de email');
  savedPh('cf-api-token', data.cloudflare_api_token_set, 'Seu API Token do Cloudflare');

  // Gmail auth status chip
  const g = document.getElementById('gmail-status');
  if (g) {
    if (data.gmail_authorized) { g.className = 'email-tag verified'; g.textContent = 'autorizado'; }
    else if (data.gmail_client_secret_set) { g.className = 'email-tag risky'; g.textContent = 'rode: mariana gmail auth'; }
    else { g.className = 'email-tag guess'; g.textContent = 'não configurado'; }
  }
  tag('reoon-status', data.reoon_api_key_set, 'configurado');
  tag('zerobounce-status', data.zerobounce_api_key_set, 'configurado');
  tag('hunter-status', data.hunter_api_key_set, 'configurado');
}

function saveGmail() {
  const payload = {GMAIL_CLIENT_ID: document.getElementById('gmail-id').value.trim()};
  const sec = document.getElementById('gmail-secret').value;
  if (sec) payload.GMAIL_CLIENT_SECRET = sec;
  saveEnv(payload, 'Gmail salvo. Agora rode "mariana gmail auth" no terminal.').then(loadSettings);
}

function saveSmtp() {
  const payload = {
    SMTP_HOST: document.getElementById('smtp-host').value.trim(),
    SMTP_PORT: document.getElementById('smtp-port').value.trim(),
    SMTP_USERNAME: document.getElementById('smtp-user').value.trim(),
  };
  const pass = document.getElementById('smtp-pass').value;
  if (pass) payload.SMTP_PASSWORD = pass;
  saveEnv(payload, 'SMTP salvo.').then(loadSettings);
}

function saveVerifiers() {
  const payload = {};
  const r = document.getElementById('reoon-key').value;
  const z = document.getElementById('zerobounce-key').value;
  const h = document.getElementById('hunter-key').value;
  if (r) payload.REOON_API_KEY = r;
  if (z) payload.ZEROBOUNCE_API_KEY = z;
  if (h) payload.HUNTER_API_KEY = h;
  if (!Object.keys(payload).length) { showToast('Coloque pelo menos uma chave.', 'error'); return; }
  saveEnv(payload, 'Chaves de verificação salvas.').then(loadSettings);
}

async function saveEnv(payload, okMsg) {
  const data = await api('/api/settings/env', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  });
  if (data && data.success) showToast(okMsg, 'success');
  else showToast((data && data.message) || 'Não salvou. O painel ainda está rodando?', 'error');
}

function saveInstantly() {
  saveEnv({INSTANTLY_API_KEY: document.getElementById('instantly-key').value.trim()}, 'Chave do Instantly salva.');
}

function saveCloudflare() {
  saveEnv({
    CLOUDFLARE_ACCOUNT_ID: document.getElementById('cf-account-id').value.trim(),
    CLOUDFLARE_API_TOKEN: document.getElementById('cf-api-token').value.trim()
  }, 'Cloudflare salvo.');
}

async function testInstantly() {
  const key = document.getElementById('instantly-key').value.trim();
  const el = document.getElementById('instantly-test-result');
  el.innerHTML = '<div class="test-result pending">Testando&hellip;</div>';
  const data = await api('/api/settings/test-instantly', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({api_key: key})
  });
  if (!data) {
    el.innerHTML = '<div class="test-result error">Não deu para falar com o servidor do painel.</div>';
    return;
  }
  el.innerHTML = '<div class="test-result ' + (data.success ? 'success' : 'error') + '">' + escHtml(data.message) + '</div>';
}

// ── Controls ──

async function loadMarianaStatus() {
  const data = await api('/api/harvey/status');
  const headerDot = document.getElementById('header-dot');
  const headerText = document.getElementById('header-status-text');

  if (!data) {
    headerDot.className = 'status-dot offline';
    headerText.textContent = 'Desconectado';
    return;
  }
  const running = !!data.running;

  headerDot.className = 'status-dot ' + (running ? 'running' : 'stopped');
  headerText.textContent = running ? 'Mariana trabalhando' : 'Mariana parada';
  document.getElementById('control-dot').className = 'dot ' + (running ? 'running' : 'stopped');
  const label = document.getElementById('control-label');
  label.className = 'label ' + (running ? 'running' : 'stopped');
  label.textContent = running ? 'Trabalhando' : 'Parada';

  const meta = document.getElementById('control-meta');
  if (running && data.pid) {
    let info = 'PID ' + escHtml(String(data.pid));
    if (data.started_at) info += ' &middot; ligada em ' + formatDate(data.started_at);
    meta.innerHTML = info;
  } else {
    meta.innerHTML = 'A Mariana acorda a cada poucos minutos, faz o que precisa e volta a dormir.';
  }

  document.getElementById('btn-start').style.display = running ? 'none' : '';
  document.getElementById('btn-stop').style.display = running ? '' : 'none';
}

async function startMariana() {
  const btn = document.getElementById('btn-start');
  btn.disabled = true;
  const data = await api('/api/harvey/start', {method: 'POST'});
  if (data && data.success) showToast('Mariana ligada.', 'success');
  else showToast((data && data.message) || 'Não deu para ligar.', 'error');
  btn.disabled = false;
  loadMarianaStatus();
}

async function stopMariana() {
  const btn = document.getElementById('btn-stop');
  btn.disabled = true;
  const data = await api('/api/harvey/stop', {method: 'POST'});
  if (data && data.success) showToast('Mariana parada.', 'success');
  else showToast((data && data.message) || 'Não deu para parar.', 'error');
  btn.disabled = false;
  loadMarianaStatus();
}

async function loadLogs() {
  const data = await api('/api/harvey/logs');
  const el = document.getElementById('log-viewer');
  if (data && data.lines && data.lines.length) {
    const stick = el.scrollTop + el.clientHeight >= el.scrollHeight - 30;
    el.textContent = data.lines.join('\n');
    if (stick) el.scrollTop = el.scrollHeight;
  } else {
    el.textContent = 'Nenhum registro ainda. Ligue a Mariana para ver a atividade.';
  }
}

// ── Pipeline data ──

async function loadStats() {
  const grid = document.getElementById('stats-grid');
  const data = await api('/api/stats');
  if (!data) { grid.innerHTML = offlineState(); return; }
  if (data.error) {
    grid.innerHTML = emptyState('&#9670;', 'Ainda sem dados no funil',
      'Ligue a Mariana na aba <b>Controles</b> e ela começa a prospectar, escrever e preparar os envios.');
    return;
  }
  const p = data.prospects || {}, c = data.campaigns || {}, v = data.conversations || {};
  const chips = (map) => {
    const entries = Object.entries(map || {});
    if (!entries.length) return '<span class="chip muted">nada ainda</span>';
    return entries.map(([k, n]) =>
      '<span class="chip">' + escHtml(k) + ' <b>' + escHtml(String(n)) + '</b></span>'
    ).join('');
  };
  const card = (label, value, breakdown) =>
    '<div class="stat-card"><div class="label">' + label + '</div>' +
    '<div class="value">' + value + '</div>' +
    '<div class="breakdown">' + breakdown + '</div></div>';

  grid.innerHTML =
    card('Leads', p.total || 0, chips(p.by_status)) +
    card('Campanhas', c.total || 0, chips(c.by_status)) +
    card('Conversas', v.total || 0, chips(v.by_status)) +
    card('Ações registradas', data.actions_total || 0, brainCallChips(data));
}

// Calls today per subscription — each labelled with the provider it ran on.
function brainCallChips(data) {
  const chip = (label, n) => '<span class="chip">' + label + ' chamadas hoje <b>' + escHtml(String(n || 0)) + '</b></span>';
  const codex = data.codex_calls_today || 0;
  const st = data.brain_status || {};
  // A paused brain must not look healthy: say so, and why.
  const paused = st.status === 'paused'
    ? '<span class="chip" title="' + escHtml(st.reason || '') + '">' +
      escHtml(st.provider === 'codex' ? 'Codex' : 'Cérebro') + ' <b>pausado</b>: ' +
      escHtml((st.reason || '').slice(0, 120)) + '</span>'
    : '';
  if (data.brain_provider === 'codex') {
    return paused + chip('Codex', codex) + (data.claude_calls_today ? chip('Claude', data.claude_calls_today) : '');
  }
  return paused + chip('Claude', data.claude_calls_today) + (codex ? chip('Codex', codex) : '');
}

function fmtTokens(n) {
  n = n || 0;
  if (n >= 1e9) return (n / 1e9).toFixed(1) + 'B';
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'k';
  return String(n);
}


function emailTag(p) {
  if (!p.email) return '';
  // Fall back to the legacy boolean for rows predating email_status.
  const status = p.email_status || (p.email_verified ? 'verified' : 'guess');
  if (!STATUS[status]) return '';
  const m = statusMeta(status);
  return ' <span class="badge t-' + m.tone + '" style="margin-left:6px">' + escHtml(m.label) + '</span>';
}

// Quota gauges for the ACTIVE provider only: Claude's are the numbers
// `/usage` shows in Claude Code; Codex's are the ChatGPT plan's limits.
// When they can't be read, say so rather than hiding the card.
function quotaCardHtml(data) {
  const provider = data && data.quota_provider;
  if (!provider) return '';
  const title = provider === 'codex' ? 'Cota do Codex (plano do ChatGPT)' : 'Cota da assinatura do Claude';
  let html = '<h2>' + escHtml(title) + '</h2>';
  if (!data.quota || !Object.keys(data.quota).length) {
    const why = provider === 'codex'
      ? "Cota indisponível: a Mariana não conseguiu ler os limites do seu plano do ChatGPT (confira o codex login, a versão do Codex CLI e a rede)."
      : "Cota indisponível: a Mariana não conseguiu ler os limites da sua assinatura do Claude (confira o claude login e a rede).";
    return html + '<p class="muted">' + escHtml(why) + ' Enquanto isso, o limite conta as chamadas da própria Mariana.</p>';
  }
  const labels = {five_hour: 'Janela de 5 horas', seven_day: 'Semanal', primary: 'Janela principal',
                  secondary: 'Janela secundária', limit_reached: 'Limite de uso atingido'};
  for (const [key, w] of Object.entries(data.quota)) {
    const pct = Math.min(100, Math.max(0, w.utilization || 0));
    const color = pct >= 80 ? 'yellow' : 'green';
    const resets = w.resets_at ? 'renova ' + formatDate(w.resets_at) : '';
    html += '<div class="progress-wrap">' +
      '<div class="progress-label">' +
        '<span class="text">' + escHtml(labels[key] || key) + (resets ? ' &middot; ' + escHtml(resets) : '') + '</span>' +
        '<span class="pct">' + pct.toFixed(0) + '%</span>' +
      '</div>' +
      '<div class="progress-bar"><div class="progress-fill ' + color + '" style="width:' + pct + '%"></div></div>' +
    '</div>';
  }
  return html;
}

async function loadUsage() {
  const data = await api('/api/usage');
  const statsEl = document.getElementById('usage-stats');
  if (!data) { statsEl.innerHTML = offlineState(); return; }

  const quotaEl = document.getElementById('usage-quota');
  const qHtml = quotaCardHtml(data);
  quotaEl.innerHTML = qHtml;
  quotaEl.style.display = qHtml ? 'block' : 'none';

  // Totals cards — usage-first (calls is the headline; tokens as chips).
  // No dollars: on a subscription plan usage isn't billed per token.
  const t = data.totals || {};
  const card = (label, p) => {
    p = p || {};
    return '<div class="stat-card"><div class="label">' + label + '</div>' +
      '<div class="value">' + (p.calls || 0) + '</div>' +
      '<div class="breakdown">' +
        '<span class="chip">chamadas</span>' +
        '<span class="chip">saída <b>' + fmtTokens(p.output_tokens) + '</b></span>' +
        '<span class="chip">entrada <b>' + fmtTokens(p.input_tokens) + '</b></span>' +
        '<span class="chip">cache <b>' + fmtTokens(p.cache_read_tokens) + '</b></span>' +
      '</div></div>';
  };
  statsEl.innerHTML = card('Hoje', t.today) + card('Últimos 7 dias', t.week) + card('Últimos 30 dias', t.month);

  // Daily bars — output tokens per day (the work done)
  const dailyEl = document.getElementById('usage-daily');
  const days = data.by_day || [];
  if (days.length) {
    const maxOut = Math.max(...days.map(d => d.output_tokens || 0), 1);
    let dHtml = '<h2>Tokens de saída por dia (30 dias)</h2>';
    for (const d of days.slice(-30)) {
      const pct = Math.max(2, (d.output_tokens || 0) / maxOut * 100);
      dHtml += '<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;font-size:12px">' +
        '<span class="muted" style="width:78px;flex-shrink:0;font-family:var(--mono)">' + escHtml(d.day || '') + '</span>' +
        '<div style="flex:1;background:rgba(255,255,255,0.05);border-radius:99px;height:10px;overflow:hidden">' +
          '<div style="width:' + pct + '%;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--accent-deep),var(--accent))"></div>' +
        '</div>' +
        '<span style="width:130px;text-align:right;font-variant-numeric:tabular-nums">' + fmtTokens(d.output_tokens) + ' saída' +
          ' <span class="muted">&middot; ' + (d.calls || 0) + ' chamadas</span></span>' +
      '</div>';
    }
    dailyEl.innerHTML = dHtml;
    dailyEl.style.display = 'block';
  } else {
    dailyEl.style.display = 'none';
  }

  // Breakdown tables — calls + tokens, no cost column
  const tablesEl = document.getElementById('usage-tables');
  const table = (title, rows, keyName, label) => {
    if (!rows || !rows.length) return '';
    let h = '<div class="card"><h2>' + title + '</h2><div class="table-card"><table><thead><tr>' +
      '<th>' + (label || keyName) + '</th><th>Chamadas</th><th>Entrada</th><th>Saída</th><th>Cache</th>' +
      '</tr></thead><tbody>';
    for (const r of rows) {
      h += '<tr><td>' + escHtml(String(r[keyName.toLowerCase()] || '')) + '</td>' +
        '<td>' + (r.calls || 0) + '</td>' +
        '<td class="muted">' + fmtTokens(r.input_tokens) + '</td>' +
        '<td>' + fmtTokens(r.output_tokens) + '</td>' +
        '<td class="muted">' + fmtTokens(r.cache_read_tokens) + '</td></tr>';
    }
    return h + '</tbody></table></div></div>';
  };

  const anyRows = (data.by_agent || []).length || (data.by_task || []).length;
  if (!anyRows) {
    tablesEl.innerHTML = emptyState('&#9680;', 'Nenhum uso registrado ainda',
      'Quando a Mariana começar a chamar o modelo (Claude ou Codex), cada chamada aparece aqui com tokens por provedor, agente e tarefa.');
  } else {
    const providers = data.by_provider || [];
    const showProviders = providers.length > 1 || (providers.length === 1 && providers[0].provider !== 'claude');
    tablesEl.innerHTML =
      (showProviders ? table('Por provedor (30 dias)', providers, 'Provider', 'Provedor') : '') +
      table('Por agente (30 dias)', data.by_agent, 'Agent', 'Agente') +
      table('Por tarefa (30 dias)', data.by_task, 'Task', 'Tarefa') +
      table('Por modelo (30 dias)', data.by_model, 'Model', 'Modelo');
  }
}

// ── Outbox: a decisions desk, not a wall of drafts ──
//
// Approving mail is a queue of one-at-a-time judgements. Showing all of them
// stacked invites a single "approve all" reflex, which is exactly the review
// the approval ladder exists to prevent. One email fills the pane; the rest
// wait in the rail.

async function loadOutbox() {
  const data = await api('/api/outbox');
  const banner = document.getElementById('outbox-banner');
  const desk = document.getElementById('outbox-desk');
  const list = document.getElementById('outbox-list');
  const actions = document.getElementById('outbox-actions');
  if (!data) { desk.innerHTML = offlineState(); list.innerHTML = ''; return; }

  const pending = data.pending || [];
  _desk.items = pending;
  if (_desk.i >= pending.length) _desk.i = Math.max(0, pending.length - 1);
  navCount('nav-outbox', pending.length);

  actions.innerHTML =
    (pending.length && !data.paused
      ? '<button class="btn btn-primary btn-sm" onclick="outboxApproveAll()">Aprovar todos ' +
        pending.length + '</button>' : '') +
    (data.paused
      ? '<button class="btn btn-secondary btn-sm" onclick="sendingToggle(\'resume\')">' +
        'Retomar envios</button>'
      : '<button class="btn btn-secondary btn-sm" onclick="sendingToggle(\'pause\')">' +
        'Pausar todos os envios</button>');

  // The kill switch gets a banner only when it's actually on — a permanent
  // bar for a thing that isn't happening is just noise.
  banner.innerHTML = data.paused
    ? '<div class="card" style="border-color:var(--red);margin-bottom:16px">' +
        '<h2 style="color:var(--red)">&#9888; Envios pausados</h2>' +
        '<p style="color:var(--text-2);font-size:13px">' + escHtml(data.paused) +
        '. Os emails aprovados esperam na fila até você retomar.</p></div>'
    : '';

  desk.innerHTML = pending.length ? renderDesk(pending, _desk.i) :
    '<div class="card">' + emptyState('&#10003;', 'Nada para revisar',
      'Todo rascunho de email da Mariana chega aqui primeiro. Aprovou, ele sai no horário agendado.') +
    '</div>';

  const table = (title, rows, cols) => {
    if (!rows || !rows.length) return '';
    let h = '<div class="card"><h2>' + title + '</h2><div class="table-card"><table><thead><tr>' +
      cols.map(c => '<th>' + c[0] + '</th>').join('') + '</tr></thead><tbody>';
    for (const r of rows) {
      h += '<tr>' + cols.map(c => '<td' + (c[2] ? ' class="muted"' : '') + '>' +
        (c[3] ? c[1](r) : escHtml(String(c[1](r) ?? ''))) + '</td>').join('') + '</tr>';
    }
    return h + '</tbody></table></div></div>';
  };

  list.innerHTML =
    table('Aprovados e agendados', data.approved, [
      ['Para', r => r.to_email], ['Etapa', r => r.step], ['Assunto', r => r.subject],
      ['Sai em', r => formatDate(r.send_at), true],
    ]) +
    table('Enviados recentemente', data.sent, [
      ['Para', r => r.to_email], ['Etapa', r => r.step], ['Assunto', r => r.subject],
      ['Enviado', r => formatDate(r.sent_at), true],
    ]) +
    table('Não saíram', data.failed, [
      ['Para', r => r.to_email], ['Status', r => badge(r.status), false, true],
      ['Motivo', r => r.error, true], ['Atualizado', r => formatDate(r.updated_at), true],
    ]);
}

function renderDesk(items, i) {
  const cur = items[i];
  const rail = items.map((it, n) =>
    '<div class="desk-item ' + (n === i ? 'active' : '') + '" onclick="deskGo(' + n + ')">' +
      '<div class="to">' + escHtml(it.to_email) + '</div>' +
      '<div class="sub">' + escHtml(it.subject || '(sem assunto)') + '</div>' +
    '</div>').join('');

  return '<div class="desk">' +
    '<div class="desk-list">' + rail + '</div>' +
    '<div class="desk-pane">' +
      '<div class="to-line">Para <b>' + escHtml(cur.to_email) + '</b> &middot; etapa ' +
        cur.step + ' (' + escHtml(cur.kind) + ') &middot; sai em ' +
        formatDate(cur.send_at) + '</div>' +
      '<div class="subject">' + escHtml(cur.subject || '(sem assunto)') + '</div>' +
      '<div class="body">' + escHtml(cur.body) + '</div>' +
      '<div class="desk-actions">' +
        '<button class="btn btn-primary" onclick="outboxAct(\'' + cur.id + '\',\'approve\')">' +
          'Aprovar <kbd>A</kbd></button>' +
        '<button class="btn btn-secondary" onclick="outboxAct(\'' + cur.id + '\',\'reject\')">' +
          'Recusar <kbd>R</kbd></button>' +
        '<span class="muted" style="font-size:12px;margin-left:auto">' +
          (i + 1) + ' de ' + items.length + '</span>' +
      '</div>' +
    '</div></div>';
}

function deskGo(n) {
  if (n < 0 || n >= _desk.items.length) return;
  _desk.i = n;
  document.getElementById('outbox-desk').innerHTML = renderDesk(_desk.items, n);
}

// Keyboard review. Ignored while typing into a field, so Settings still works.
document.addEventListener('keydown', e => {
  if (currentTab !== 'outbox' || e.metaKey || e.ctrlKey || e.altKey) return;
  const tag = (e.target.tagName || '').toLowerCase();
  if (tag === 'input' || tag === 'textarea' || e.target.isContentEditable) return;
  const cur = _desk.items[_desk.i];
  const k = e.key.toLowerCase();
  if (k === 'j') { e.preventDefault(); deskGo(_desk.i + 1); }
  else if (k === 'k') { e.preventDefault(); deskGo(_desk.i - 1); }
  else if (k === 'a' && cur) { e.preventDefault(); outboxAct(cur.id, 'approve'); }
  else if (k === 'r' && cur) { e.preventDefault(); outboxAct(cur.id, 'reject'); }
});

async function outboxAct(id, action) {
  const data = await api('/api/outbox/' + encodeURIComponent(id) + '/' + action, {method: 'POST'});
  if (data && data.success) showToast(action === 'approve' ? 'Aprovado. Sai no horário agendado.' : 'Recusado.', 'success');
  else showToast('Não deu certo.', 'error');
  loadOutbox();
}

async function outboxApproveAll() {
  const data = await api('/api/outbox/approve-all', {method: 'POST'});
  if (data && data.success) showToast(data.approved + ' email(s) aprovado(s).', 'success');
  else showToast('Não deu para aprovar todos.', 'error');
  loadOutbox();
}

async function sendingToggle(action) {
  const data = await api('/api/sending/' + action, {method: 'POST'});
  if (data && data.success) showToast(action === 'pause' ? 'Envios pausados.' : 'Envios retomados.', 'success');
  else showToast('Não deu certo.', 'error');
  loadOutbox();
}

async function loadCompanies() {
  companyDrill = false;
  const el = document.getElementById('companies-list');
  const data = await api('/api/companies');
  if (!data) { el.innerHTML = offlineState(); return; }
  _companies = data;
  if (!data.length) {
    el.innerHTML = emptyState('&#9906;', 'Nenhuma empresa ainda',
      'A Mariana ainda não pesquisou empresas. Rode a busca na aba <b>Descobrir</b> ou ligue a Mariana na aba <b>Controles</b>.');
    return;
  }
  let html = '<div class="table-card"><table><thead><tr><th>Empresa</th><th>Domínio</th><th>Segmento</th><th>Tamanho</th><th>Local</th><th>Contatos</th><th>Origem</th><th>Adicionada</th></tr></thead><tbody>';
  data.forEach((c, i) => {
    const website = c.website || (c.domain ? 'https://' + c.domain : '');
    const nameLink = website
      ? '<a href="' + escHtml(website) + '" target="_blank" rel="noopener" onclick="event.stopPropagation()">' + escHtml(c.name) + '</a>'
      : escHtml(c.name);
    html += '<tr style="cursor:pointer" onclick="showCompanyContacts(' + i + ')">' +
      '<td>' + nameLink + '</td><td class="muted">' + escHtml(c.domain) + '</td><td>' + escHtml(c.industry) + '</td>' +
      '<td>' + escHtml(c.company_size) + '</td><td>' + escHtml(c.location) + '</td>' +
      '<td>' + (c.contact_count || 0) + '</td><td class="muted">' + escHtml(c.source) + '</td>' +
      '<td class="muted">' + formatDate(c.created_at) + '</td></tr>';
  });
  el.innerHTML = html + '</tbody></table></div>';
}

async function showCompanyContacts(index) {
  const company = _companies[index];
  if (!company) return;
  companyDrill = true;
  const el = document.getElementById('companies-list');
  const data = await api('/api/companies/' + encodeURIComponent(company.id) + '/contacts');
  let html = '<div class="card"><h2>' + escHtml(company.name) + ': contatos</h2>' +
    '<button class="btn btn-secondary btn-sm" onclick="loadCompanies()" style="margin-bottom:16px">&larr; Voltar para Empresas</button>';
  if (!data || !data.length) {
    html += '<p style="color:var(--text-3);font-size:13px">Nenhum contato encontrado nesta empresa ainda.</p></div>';
  } else {
    html += '<div class="table-card"><table><thead><tr><th>Nome</th><th>Cargo</th><th>Email</th><th>Telefone</th><th>LinkedIn</th><th>Status</th><th>Origem</th></tr></thead><tbody>';
    for (const p of data) {
      const emailIcon = emailTag(p);
      const phoneIcon = p.phone_verified ? ' <span class="verified">&#10003;</span>' : '';
      html += '<tr><td>' + escHtml(p.first_name) + ' ' + escHtml(p.last_name) + '</td>' +
        '<td>' + escHtml(p.title) + '</td><td>' + escHtml(p.email) + emailIcon + '</td>' +
        '<td>' + escHtml(p.phone) + phoneIcon + '</td>' +
        '<td>' + (p.linkedin_url ? '<a href="' + escHtml(p.linkedin_url) + '" target="_blank" rel="noopener">Perfil</a>' : '') + '</td>' +
        '<td>' + badge(p.status) + '</td><td class="muted">' + escHtml(p.source) + '</td></tr>';
    }
    html += '</tbody></table></div></div>';
  }
  el.innerHTML = html;
}

async function submitFeedback(entityType, entityId, promptText) {
  const comment = prompt(promptText || 'Seu comentário:');
  if (!comment) return;
  const data = await api('/api/feedback', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({entity_type: entityType, entity_id: entityId, comment: comment})
  });
  if (data && data.success) showToast('Comentário salvo. A Mariana vai levar em conta.', 'success');
  else showToast((data && data.message) || 'Não deu para salvar o comentário.', 'error');
}

function fbProspect(i) {
  const p = _prospects[i];
  if (p) submitFeedback('contact', p.id, 'Comentário sobre este contato:');
}

function fbCampaign(i) {
  const c = _campaigns[i];
  if (c) submitFeedback('campaign', c.id, 'Comentário sobre esta campanha:');
}

async function loadProspects() {
  const el = document.getElementById('prospects-table');
  const data = await api('/api/prospects');
  if (!data) { el.innerHTML = offlineState(); return; }
  _prospects = data;
  if (!data.length) {
    el.innerHTML = emptyState('&#9673;', 'Nenhum contato ainda',
      'A Mariana ainda não encontrou leads. Com ela ligada, o Scout procura pessoas que batem com o seu perfil de cliente.');
    return;
  }
  let html = '<div class="table-card"><table><thead><tr><th>Nome</th><th>Cargo</th><th>Empresa</th><th>Email</th><th>Telefone</th><th>Status</th><th>Origem</th><th>Adicionado</th><th></th></tr></thead><tbody>';
  data.forEach((p, i) => {
    const emailV = p.email ? (escHtml(p.email) + emailTag(p)) : '';
    const phoneV = p.phone ? (escHtml(p.phone) + (p.phone_verified ? ' <span class="verified">&#10003;</span>' : '')) : '';
    html += '<tr><td>' + escHtml(p.first_name) + ' ' + escHtml(p.last_name) + '</td>' +
      '<td>' + escHtml(p.title) + '</td><td>' + escHtml(p.company) + '</td>' +
      '<td>' + emailV + '</td><td>' + phoneV + '</td><td>' + badge(p.status) + '</td>' +
      '<td class="muted">' + escHtml(p.source) + '</td><td class="muted">' + formatDate(p.created_at) + '</td>' +
      '<td><button class="btn btn-secondary btn-sm" onclick="fbProspect(' + i + ')">Comentar</button></td></tr>';
  });
  el.innerHTML = html + '</tbody></table></div>';
}

async function loadCampaigns() {
  const el = document.getElementById('campaigns-list');
  const data = await api('/api/campaigns');
  if (!data) { el.innerHTML = offlineState(); return; }
  _campaigns = data;
  if (!data.length) {
    el.innerHTML = emptyState('&#9993;', 'Nenhuma campanha ainda',
      'O Writer ainda não escreveu sequências. Ele começa sozinho quando houver leads pontuados.');
    return;
  }
  let html = '';
  data.forEach((c, i) => {
    let stepsHtml = '';
    for (const step of (c.sequence || [])) {
      stepsHtml += '<div class="email-step"><div class="step-num">Email ' + escHtml(String(step.step || '?')) +
        (step.delay_days ? ' &middot; sai depois de ' + escHtml(String(step.delay_days)) + ' dias' : '') + '</div>' +
        '<div class="subject">' + escHtml(step.subject) + '</div>' +
        '<div class="body">' + escHtml(step.body) + '</div></div>';
    }
    const pc = (c.prospect_ids || []).length;
    html += '<div class="campaign-card"><h3>' + escHtml(c.name || 'Campanha sem nome') + '</h3>' +
      '<div class="meta">' + badge(c.status) + '<span>' + escHtml(c.channel || 'email') + '</span>' +
      '<span>' + pc + (pc !== 1 ? ' leads' : ' lead') + '</span><span>' + formatDate(c.created_at) + '</span>' +
      '<button class="btn btn-secondary btn-sm" onclick="fbCampaign(' + i + ')">Comentar</button></div>' +
      (stepsHtml || '<p style="color:var(--text-3);font-size:13px">Esta campanha não tem emails.</p>') + '</div>';
  });
  el.innerHTML = html;
}

async function loadConversations() {
  const el = document.getElementById('conversations-list');
  const data = await api('/api/conversations');
  if (!data) { el.innerHTML = offlineState(); return; }
  if (!data.length) {
    el.innerHTML = emptyState('&#9737;', 'Nenhuma conversa ainda',
      'Ninguém respondeu até agora. Quando responderem, a Mariana classifica e rascunha a resposta, e cada conversa aparece aqui.');
    return;
  }
  let html = '';
  for (const c of data) {
    let threadHtml = '';
    for (const msg of (c.thread || [])) {
      const cls = msg.sender === 'harvey' ? 'sent' : 'received';
      const who = msg.sender === 'harvey' ? 'você' : (msg.sender === 'prospect' ? 'cliente' : msg.sender);
      threadHtml += '<div class="thread-msg ' + cls + '"><div class="sender">' + escHtml(who) +
        ' &middot; ' + formatDate(msg.timestamp) + '</div>' + escHtml(msg.content) + '</div>';
    }
    const name = [c.first_name, c.last_name].filter(Boolean).join(' ') || 'Sem nome';
    html += '<div class="convo-card"><h3>' + escHtml(name) +
      (c.company ? ' <span style="color:var(--text-3);font-weight:500">&mdash; ' + escHtml(c.company) + '</span>' : '') + '</h3>' +
      '<div class="meta">' + badge(c.status) + (c.intent ? badge(c.intent) : '') +
      '<span>' + escHtml(c.prospect_email || '') + '</span><span>' + formatDate(c.updated_at) + '</span></div>' +
      (threadHtml || '<p style="color:var(--text-3);font-size:13px">Nenhuma mensagem nesta conversa ainda.</p>') +
      '<div class="desk-actions" style="margin-top:10px">' +
        '<button class="btn btn-secondary btn-sm" onclick="convoProposal(\'' + c.id + '\')">Gerar proposta</button>' +
        '<button class="btn btn-primary btn-sm" onclick="convoWon(\'' + c.id + '\')">Fechou</button>' +
      '</div></div>';
  }
  el.innerHTML = html;
}

async function loadActivity() {
  const el = document.getElementById('activity-list');
  const data = await api('/api/activity');
  if (!data) { el.innerHTML = offlineState(); return; }
  if (!data.length) {
    el.innerHTML = emptyState('&#9202;', 'Nenhuma atividade ainda',
      'A Mariana ainda não fez nada. Cada lead encontrado, email escrito e resposta tratada aparece aqui na hora.');
    return;
  }
  let html = '<div class="activity-feed">';
  for (const a of data) {
    html += '<div class="activity-item"><span class="time">' + formatDate(a.created_at) + '</span>' +
      '<span class="agent">' + escHtml(a.agent) + '</span>' +
      '<span class="action">' + escHtml(String(a.action_type).replace(/_/g, ' ')) + '</span></div>';
  }
  el.innerHTML = html + '</div>';
}

// ── Init & live refresh ──

loadToday();
loadSetupStatus();
loadRuns();
loadTodayActivity();
loadMarianaStatus();

// Agent status: quick poll
setInterval(loadMarianaStatus, 8000);

// Nav counts stay live wherever you are, so "something needs me" is visible
// from any tab without polling that tab's contents.
setInterval(async () => {
  if (document.hidden || currentTab === 'today') return;
  const data = await api('/api/today');
  if (!data) return;
  navCount('nav-today', (data.items || []).filter(i => i.tone !== 'good').length);
  navCount('nav-outbox', (data.stats || {}).outbox_pending || 0);
}, 20000);

// Data tabs: auto-refresh live views without clobbering anything in progress.
// Outbox, settings and help are deliberately excluded — re-rendering the desk
// under someone mid-decision loses their place, and settings may be mid-edit.
setInterval(() => {
  if (document.hidden) return;
  switch (currentTab) {
    case 'today': loadToday(); loadRuns(); loadTodayActivity(); break;
    case 'companies': if (!companyDrill) loadCompanies(); break;
    case 'prospects': loadProspects(); break;
    case 'campaigns': loadCampaigns(); break;
    case 'conversations': loadConversations(); break;
    case 'activity': loadActivity(); break;
    case 'usage': loadUsage(); break;
    case 'controls': loadLogs(); break;
  }
}, 15000);


// ── Mensagens: WhatsApp / LinkedIn / Instagram ──
//
// Drafts only. The send button opens WhatsApp with the text typed in, or
// opens the profile and copies the text; the person sends it from their own
// account and marks it sent here.

const CHANNEL_LABEL = {whatsapp: 'WhatsApp', linkedin: 'LinkedIn', instagram: 'Instagram'};

async function loadChannels() {
  const el = document.getElementById('channels-list');
  const data = await api('/api/channels');
  if (!data) { el.innerHTML = offlineState(); return; }
  if (data.error) { el.innerHTML = '<div class="card">' + escHtml(data.error) + '</div>'; return; }
  const pending = data.pending || [];
  navCount('nav-channels', pending.length);
  window._channelItems = {};
  [...pending, ...(data.approved || [])].forEach(it => { window._channelItems[it.id] = it; });

  const card = it => {
    const who = [it.contact_name, it.company_name].filter(Boolean).join(' · ') || it.target;
    const note = it.note
      ? '<div class="muted" style="font-size:12px;margin:8px 0 4px">Nota do convite</div>' +
        '<div class="body" style="white-space:pre-wrap">' + escHtml(it.note) + '</div>' : '';
    const warn = it.error ? '<div style="color:var(--red);font-size:12px">' + escHtml(it.error) + '</div>' : '';
    const approve = it.status === 'pending_review'
      ? '<button class="btn btn-secondary btn-sm" onclick="channelAct(\'' + it.id + '\',\'approve\')">Aprovar</button>' : '';
    const sendLabel = it.channel === 'whatsapp' ? 'Abrir no WhatsApp' : 'Copiar e abrir perfil';
    return '<div class="card" style="margin-bottom:12px">' +
      '<div style="display:flex;justify-content:space-between;gap:8px;align-items:center">' +
        '<div><b>' + escHtml(CHANNEL_LABEL[it.channel] || it.channel) + '</b>' +
          (it.kind === 'reply' ? ' (resposta)' : it.kind === 'postjob' ? ' (pós-job)' : it.kind === 'sample' ? ' (amostra)' : '') +
          ' &middot; ' +
          escHtml(who) + ' <span class="muted">(' + escHtml(it.language || '') + ')</span></div>' +
        badge(it.status) + '</div>' + warn + note +
      (it.note ? '<div class="muted" style="font-size:12px;margin:8px 0 4px">Mensagem</div>' : '') +
      '<div class="body" style="white-space:pre-wrap;margin-top:8px">' + escHtml(it.body) + '</div>' +
      '<div class="desk-actions" style="margin-top:12px">' +
        '<button class="btn btn-primary btn-sm" onclick="channelOpen(\'' + it.id + '\')">' + sendLabel + '</button>' +
        approve +
        '<button class="btn btn-secondary btn-sm" onclick="channelAct(\'' + it.id + '\',\'sent\')">Marcar enviada</button>' +
        (it.channel === 'whatsapp' && !it.opted_in
          ? '<button class="btn btn-secondary btn-sm" onclick="channelAct(\'' + it.id + '\',\'optin\')">Deu opt-in</button>' : '') +
        '<button class="btn btn-secondary btn-sm" onclick="channelAct(\'' + it.id + '\',\'reject\')">Descartar</button>' +
      '</div></div>';
  };

  const sentRows = (data.sent || []).map(r =>
    '<tr><td>' + escHtml(CHANNEL_LABEL[r.channel] || r.channel) + '</td><td>' +
    escHtml(r.company_name || r.contact_name || r.target) + '</td><td class="muted">' +
    formatDate(r.sent_at) + '</td><td>' +
    '<button class="btn btn-secondary btn-sm" onclick="channelReplied(\'' + r.id + '\')">Respondeu</button>' +
    '</td></tr>').join('');

  el.innerHTML =
    (pending.length || (data.approved || []).length
      ? [...pending, ...(data.approved || [])].map(card).join('')
      : '<div class="card">' + emptyState('&#10003;', 'Nenhuma mensagem esperando',
          'Quando a Mariana montar uma campanha, as mensagens de WhatsApp, LinkedIn e Instagram aparecem aqui.') + '</div>') +
    (sentRows ? '<div class="card"><h2>Enviadas</h2><div class="table-card"><table><thead><tr>' +
      '<th>Canal</th><th>Para</th><th>Quando</th><th></th></tr></thead><tbody>' + sentRows +
      '</tbody></table></div></div>' : '');
}

async function channelOpen(id) {
  const it = (window._channelItems || {})[id];
  if (!it) return;
  if (it.channel !== 'whatsapp') {
    const text = it.note ? it.note + '\n\n---\n\n' + it.body : it.body;
    try { await navigator.clipboard.writeText(text); toastMsg('Texto copiado'); } catch (e) {}
  }
  window.open(it.open_url, '_blank', 'noopener');
}

function toastMsg(msg) {
  showToast(msg, 'success');
}

async function channelAct(id, action) {
  await api('/api/channels/' + encodeURIComponent(id) + '/' + action, {method: 'POST'});
  loadChannels();
}

async function channelReplied(id) {
  const text = window.prompt('Cole aqui o que a pessoa respondeu:');
  if (!text || !text.trim()) return;
  const res = await api('/api/channels/' + encodeURIComponent(id) + '/replied', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text: text}),
  });
  if (res && res.success) {
    toastMsg('Resposta registrada. Emails pendentes cancelados; rascunho de resposta em Mensagens.');
  } else {
    alert((res && res.message) || 'Não deu certo.');
  }
  loadChannels();
}

// ── Conversas → proposta / fechou ──
async function convoProposal(id) {
  showToast('Montando a proposta...', 'success');
  const r = await fetch('/api/conversations/' + encodeURIComponent(id) + '/proposal', {method: 'POST'});
  const data = await r.json().catch(() => null);
  if (data && data.success) {
    window.open('/api/proposals/' + encodeURIComponent(data.file), '_blank', 'noopener');
    showToast('Proposta pronta (aba Jobs).', 'success');
    if ((data.suggested_prices || []).length) {
      alert('Preço sugerido pelo seu histórico (confira antes de enviar): ' +
        data.suggested_prices.join(', ') + '\n\n' + (data.price_hints || []).join('\n'));
    }
  } else {
    alert('Não consegui: ' + ((data && data.message) || 'erro'));
  }
}

async function convoWon(id) {
  const value = window.prompt('Fechou. Valor do job (opcional):', '') ;
  if (value === null) return;
  const next = window.prompt('Data do próximo evento desse cliente, se tiver (AAAA-MM-DD):', '');
  await api('/api/conversations/' + encodeURIComponent(id) + '/job', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({value: value || '', next_event_date: next || ''}),
  });
  showToast('Job registrado. Montando a pasta do cliente para o Gab...', 'success');
  loadConversations();
}

// ── Jobs ──
const JOB_LABEL = {proposal: 'Proposta', won: 'Fechado', delivered: 'Entregue', lost: 'Perdido'};

async function loadJobs() {
  const el = document.getElementById('jobs-list');
  const data = await api('/api/jobs');
  if (!data) { el.innerHTML = offlineState(); return; }
  if (data.error) { el.innerHTML = '<div class="card">' + escHtml(data.error) + '</div>'; return; }
  if (!data.length) {
    el.innerHTML = '<div class="card">' + emptyState('&#127916;', 'Nenhum job ainda',
      'Em Conversas, use "Gerar proposta" ou "Fechou". O job aparece aqui.') + '</div>';
    return;
  }
  let h = '<div class="card"><div class="table-card"><table><thead><tr>' +
    '<th>Cliente</th><th>Serviço</th><th>Valor</th><th>Status</th><th>Próx. evento</th><th>Proposta</th><th></th>' +
    '</tr></thead><tbody>';
  for (const j of data) {
    const prop = j.proposal_file
      ? '<a href="/api/proposals/' + encodeURIComponent(j.proposal_file) + '" target="_blank">abrir</a>' : '';
    const btn = (action, label) => '<button class="btn btn-secondary btn-sm" onclick="jobAct(\'' +
      j.id + '\',\'' + action + '\')">' + label + '</button> ';
    h += '<tr><td><b>' + escHtml(j.company_name || j.contact_name) + '</b><br><span class="muted">' +
      escHtml(j.contact_name || '') + '</span></td><td>' + escHtml(j.service || '') + '</td><td>' +
      escHtml(j.value || '') + '</td><td>' + escHtml(JOB_LABEL[j.status] || j.status) + '</td><td>' +
      escHtml(j.next_event_date || '') + '</td><td>' + prop + '</td><td>' +
      (j.status === 'proposal' ? (j.proposal_sent_at ? '<span class="muted">enviada ' + escHtml(j.proposal_sent_at) +
          (j.followups ? ' · ' + j.followups + ' lembrete(s)' : '') + '</span><br>' : btn('proposal_sent', 'Enviei a proposta')) +
          btn('won', 'Fechou') + btn('lost', 'Perdeu') : '') +
      (j.status === 'won' ? btn('revision', 'Revisão ' + (j.revisions_used || 0) + '/' + (j.revisions_included || 2)) +
          btn('delivered', 'Entreguei') : '') +
      btn('update', 'Próx. evento') +
      '<button class="btn btn-secondary btn-sm" onclick="jobEdit(\'' + j.id + '\')">Produção</button>' +
      '</td></tr>' +
      '<tr id="jobedit-' + j.id + '" style="display:none"><td colspan="7">' + jobEditor(j) + '</td></tr>' +
      ((j.project_dir || j.notes || j.shoot_date) ? '<tr><td colspan="7" class="muted" style="font-size:12px">' +
        [j.shoot_date ? 'Gravação ' + escHtml(j.shoot_date + ' ' + (j.shoot_time || '')) : '',
         j.address ? escHtml(j.address) : '',
         j.delivery_due ? 'Entrega ' + escHtml(j.delivery_due) : '',
         j.project_dir ? 'Pasta: ' + escHtml(j.project_dir) : '',
         j.notes ? escHtml(j.notes) : ''].filter(Boolean).join(' · ') + '</td></tr>' : '');
  }
  el.innerHTML = h + '</tbody></table></div></div>';
}

const JOB_FIELDS = [['shoot_date', 'Data da gravação (AAAA-MM-DD)'], ['shoot_time', 'Horário'],
  ['address', 'Endereço'], ['onsite_contact', 'Contato no local'], ['delivery_due', 'Entrega (AAAA-MM-DD)'],
  ['revisions_included', 'Rodadas de revisão'], ['delivery_link', 'Link da entrega'],
  ['next_event_date', 'Próximo evento do cliente'], ['value', 'Valor']];

function jobEditor(j) {
  return '<div class="grid" style="display:grid;grid-template-columns:1fr 1fr;gap:8px">' +
    JOB_FIELDS.map(([k, label]) => '<label style="font-size:12px">' + label +
      '<input class="input" style="width:100%" id="jf-' + j.id + '-' + k + '" value="' +
      escHtml(j[k] == null ? '' : String(j[k])) + '"></label>').join('') +
    '<label style="font-size:12px;grid-column:1/-1">Checklist (um por linha)<textarea class="input" ' +
      'style="width:100%;min-height:90px" id="jf-' + j.id + '-checklist">' + escHtml(j.checklist || '') +
      '</textarea></label></div>' +
    '<button class="btn btn-primary btn-sm" style="margin-top:8px" onclick="jobSave(\'' + j.id + '\')">Salvar</button>';
}

function jobEdit(id) {
  const row = document.getElementById('jobedit-' + id);
  if (row) row.style.display = row.style.display === 'none' ? '' : 'none';
}

async function jobSave(id) {
  const body = {};
  for (const [k] of [...JOB_FIELDS, ['checklist']]) {
    const el = document.getElementById('jf-' + id + '-' + k);
    if (el) body[k] = el.value;
  }
  await api('/api/jobs/' + encodeURIComponent(id) + '/update', {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body),
  });
  showToast('Produção salva.', 'success');
  loadJobs();
}

async function jobAct(id, action) {
  const body = {};
  if (action === 'update') {
    const d = window.prompt('Data do próximo evento do cliente (AAAA-MM-DD):', '');
    if (!d) return;
    body.next_event_date = d;
  }
  const res = await api('/api/jobs/' + encodeURIComponent(id) + '/' + action, {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body),
  });
  if (res && res.over) alert('Passou das ' + res.revisions_included + ' rodadas combinadas. ' +
    'Deixei um rascunho avisando sobre revisão extra (aprovar em Mensagens/Outbox).');
  if (res && res.project && res.project.folder) showToast('Pasta do cliente: ' + res.project.folder, 'success');
  loadJobs();
}

// ── Números ──
function openerTable(rows) {
  if (!rows || !rows.length) return '';
  let h = '<div class="card"><h2>Por estilo de abertura</h2><div class="table-card"><table><thead><tr>' +
    '<th>Estilo</th><th>Enviadas</th><th>Aceitaram o convite</th><th>Responderam</th><th>Taxa</th></tr></thead><tbody>';
  for (const r of rows) {
    h += '<tr><td>' + escHtml(r.key) + '</td><td>' + r.sent + '</td><td>' +
      (r.invites ? r.accepted + ' (' + r.accept_rate + '%)' : '') + '</td><td>' + r.replied +
      '</td><td><b>' + r.reply_rate + '%</b></td></tr>';
  }
  return h + '</tbody></table></div></div>';
}

async function loadMetrics() {
  const el = document.getElementById('metrics-list');
  const data = await api('/api/metrics');
  if (!data) { el.innerHTML = offlineState(); return; }
  if (data.error) { el.innerHTML = '<div class="card">' + escHtml(data.error) + '</div>'; return; }
  const t = data.total || {};
  const table = (title, rows, label) => {
    if (!rows || !rows.length) return '';
    let h = '<div class="card"><h2>' + title + '</h2><div class="table-card"><table><thead><tr><th>' + label +
      '</th><th>Contatados</th><th>Responderam</th><th>Taxa</th><th>Fechados</th></tr></thead><tbody>';
    for (const r of rows) {
      h += '<tr><td>' + escHtml(r.key) + '</td><td>' + r.contacted + '</td><td>' + r.replied +
        '</td><td><b>' + r.reply_rate + '%</b></td><td>' + r.won + '</td></tr>';
    }
    return h + '</tbody></table></div></div>';
  };
  el.innerHTML =
    '<div class="card"><h2>Geral</h2><p style="font-size:15px">' + (t.contacted || 0) + ' contatados &middot; ' +
      (t.replied || 0) + ' responderam (<b>' + (t.reply_rate || 0) + '%</b>) &middot; ' +
      (t.won || 0) + ' fechados (' + (t.win_rate || 0) + '%)</p></div>' +
    table('Por mercado', data.by_market, 'Mercado') +
    table('Por canal', data.by_channel, 'Canal') +
    table('Por tipo de cliente', data.by_segment, 'Segmento') +
    openerTable(data.by_opener) +
    (t.contacted ? '' : '<div class="card">' + emptyState('&#128202;', 'Sem dados ainda',
      'Os números aparecem quando as primeiras mensagens forem enviadas.') + '</div>');
}
