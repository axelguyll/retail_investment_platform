// ─── Scoring ──────────────────────────────────────────────────────────────────

function mmNorm(arr, invert) {
  const mn = Math.min(...arr), mx = Math.max(...arr);
  if (mx === mn) return arr.map(() => 0.5);
  return arr.map(v => { const n = (v-mn)/(mx-mn); return invert ? 1-n : n; });
}

function buildMarkets() {
  const cs = RAW.map(r => +(r.cr - TREASURY).toFixed(2));
  const nEg = mmNorm(RAW.map(r=>r.eg));
  const nPg = mmNorm(RAW.map(r=>r.pg));
  const nVt = mmNorm(RAW.map(r=>r.vt), true);
  const nCs = mmNorm(cs);

  return RAW.map((r,i) => ({
    metro: r.metro, state: r.state,
    employment_growth: r.eg,
    population_growth: r.pg,
    retail_vacancy_trend: r.vt,
    cap_rate: r.cr,
    cap_rate_spread: cs[i],
    s_eg: nEg[i]*100, s_pg: nPg[i]*100, s_vt: nVt[i]*100, s_cs: nCs[i]*100,
    total_score: +( nEg[i]*100*W.eg + nPg[i]*100*W.pg + nVt[i]*100*W.vt + nCs[i]*100*W.cs ).toFixed(2),
  }))
  .sort((a,b) => b.total_score - a.total_score)
  .map((r,i) => ({...r, rank: i+1}));
}

let MARKETS = buildMarkets();

function updateScreenerCards() {
  const top    = MARKETS[0];
  const avgCap = MARKETS.reduce((s,m) => s + m.cap_rate, 0) / MARKETS.length;
  const el = id => document.getElementById(id);
  if (el('mc-top-score')) el('mc-top-score').textContent = top.total_score.toFixed(1);
  if (el('mc-top-metro')) el('mc-top-metro').textContent = `${top.metro}, ${top.state}`;
  if (el('mc-avg-cap'))   el('mc-avg-cap').textContent   = avgCap.toFixed(2) + '%';
  if (el('mc-treasury'))  el('mc-treasury').textContent  = (TREASURY * 100).toFixed(2) + '%';
}

// Called by api.js after TREASURY is updated with a live value
function rebuildMarkets() {
  MARKETS = buildMarkets();
  renderTable();
  renderTop10();
  updateScreenerCards();
}
