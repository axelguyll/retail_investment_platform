// ─── View Switch ──────────────────────────────────────────────────────────────
const VIEW_META = {
  screener:     { title:'Market Screener',   sub:'42 US metros · composite scoring model' },
  underwriting: { title:'Underwriting Tool', sub:'IRR · DSCR · Cash-on-Cash · Equity Multiple' },
};

function switchView(view, el) {
  document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  document.getElementById('view-'+view).classList.add('active');
  el.classList.add('active');
  document.getElementById('view-title').textContent    = VIEW_META[view].title;
  document.getElementById('view-subtitle').textContent = VIEW_META[view].sub;
}

// ─── API Keys Modal ───────────────────────────────────────────────────────────
const KEY_IDS = { fred:'FRED_API_KEY', bls:'BLS_API_KEY', census:'CENSUS_API_KEY' };

function openKeysModal() {
  for (const [id, storageKey] of Object.entries(KEY_IDS)) {
    const val = localStorage.getItem(storageKey) || '';
    document.getElementById('k-'+id).value = val;
    updateKeyStatus(id);
  }
  document.getElementById('keys-modal').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeKeysModal(e) {
  if (e && e.target !== document.getElementById('keys-modal')) return;
  document.getElementById('keys-modal').classList.remove('open');
  document.body.style.overflow = '';
}

function updateKeyStatus(id) {
  const val = document.getElementById('k-'+id).value.trim();
  const el  = document.getElementById('ks-'+id);
  el.textContent = val ? '●' : '○';
  el.style.color  = val ? 'var(--emerald)' : 'var(--text-3)';
}

function saveKeys() {
  for (const [id, storageKey] of Object.entries(KEY_IDS)) {
    const val = document.getElementById('k-'+id).value.trim();
    if (val) localStorage.setItem(storageKey, val);
    else     localStorage.removeItem(storageKey);
  }
  // Re-run API init so new keys take effect immediately
  initAPI();

  const msg = document.getElementById('saved-msg');
  msg.classList.add('show');
  setTimeout(() => msg.classList.remove('show'), 2200);
}

function clearKeys() {
  for (const [id, storageKey] of Object.entries(KEY_IDS)) {
    localStorage.removeItem(storageKey);
    document.getElementById('k-'+id).value = '';
    updateKeyStatus(id);
  }
  updateSidebarSources();
}

function updateSidebarSources() {
  const hasFred   = !!localStorage.getItem('FRED_API_KEY');
  const hasBls    = !!localStorage.getItem('BLS_API_KEY');
  const hasCensus = !!localStorage.getItem('CENSUS_API_KEY');

  const dots = document.querySelectorAll('.source-dot');
  const rows = document.querySelectorAll('.source-row');

  const states = [
    { dot:dots[0], row:rows[0], live:hasFred,   liveLabel:'Treasury Rate (FRED)', fallLabel:'Treasury Rate (CSV)' },
    { dot:dots[1], row:rows[1], live:hasBls,    liveLabel:'Employment (BLS)',      fallLabel:'Employment (CSV)' },
    { dot:dots[2], row:rows[2], live:hasCensus, liveLabel:'Population (Census)',   fallLabel:'Population (CSV)' },
    { dot:dots[3], row:rows[3], live:false,     liveLabel:'Vacancy / Cap Rate',    fallLabel:'Vacancy / Cap Rate' },
  ];

  states.forEach(({ dot, row, live, liveLabel, fallLabel }) => {
    dot.className = 'source-dot ' + (live ? 'live' : 'fallback');
    const textNode = [...row.childNodes].find(n => n.nodeType === 3);
    if (textNode) textNode.textContent = live ? liveLabel : fallLabel;
  });
}

// ─── Init ─────────────────────────────────────────────────────────────────────
document.getElementById('hdr-date').textContent =
  new Date().toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric',year:'numeric'});

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeKeysModal({target: document.getElementById('keys-modal')});
});

renderTable();
renderTop10();
updateScreenerCards();
initAPI(); // async: fetches FRED treasury rate if key is stored, then rebuilds
