// ─── Table State ──────────────────────────────────────────────────────────────
let sortKey = 'rank', sortAsc = true, filterStr = '', selectedMetro = null;

function renderTable() {
  let data = [...MARKETS];
  if (filterStr) {
    const q = filterStr.toLowerCase();
    data = data.filter(r => r.metro.toLowerCase().includes(q) || r.state.toLowerCase().includes(q));
  }
  if (sortKey !== 'rank') {
    data.sort((a,b) => {
      const av = a[sortKey], bv = b[sortKey];
      return sortAsc ? (av>bv?1:-1) : (av<bv?1:-1);
    });
  } else if (!sortAsc) {
    data.reverse();
  }

  const body = document.getElementById('markets-body');
  body.innerHTML = data.map(r => {
    const rk  = r.rank === 1 ? 'rank-gold' : r.rank === 2 ? 'rank-silv' : r.rank === 3 ? 'rank-brnz' : 'rank-other';
    const vtC = r.retail_vacancy_trend < 0 ? 'pos' : r.retail_vacancy_trend > 0 ? 'neg' : 'neu';
    const vtS = r.retail_vacancy_trend > 0 ? '+' : '';
    const egC = r.employment_growth > 0 ? 'pos' : r.employment_growth < 0 ? 'neg' : 'neu';
    const pgC = r.population_growth > 0 ? 'pos' : r.population_growth < 0 ? 'neg' : 'neu';
    const sel = selectedMetro === r.metro ? 'row-selected' : '';
    return `<tr class="${sel}" onclick="selectMetro('${r.metro.replace(/'/g,"\\'")}')">
      <td><span class="rank-badge ${rk}">${r.rank}</span></td>
      <td style="font-weight:500">${r.metro}</td>
      <td class="mono" style="color:var(--text-3)">${r.state}</td>
      <td>
        <div class="score-cell">
          <div class="score-bar"><div class="score-fill" style="width:${r.total_score}%"></div></div>
          <span class="score-num">${r.total_score.toFixed(1)}</span>
        </div>
      </td>
      <td class="mono ${egC}">${r.employment_growth>0?'+':''}${r.employment_growth.toFixed(2)}%</td>
      <td class="mono ${pgC}">${r.population_growth>0?'+':''}${r.population_growth.toFixed(2)}%</td>
      <td class="mono ${vtC}">${vtS}${r.retail_vacancy_trend.toFixed(1)} pp</td>
      <td class="mono pos">+${r.cap_rate_spread.toFixed(2)}%</td>
      <td class="mono">${r.cap_rate.toFixed(2)}%</td>
    </tr>`;
  }).join('');
}

function filterTable(v) { filterStr = v; renderTable(); }

function sortBy(key) {
  document.querySelectorAll('thead th').forEach(th => th.classList.remove('col-sorted'));
  const th = document.getElementById('th-'+key);
  if (th) th.classList.add('col-sorted');
  if (sortKey === key) { sortAsc = !sortAsc; }
  else { sortKey = key; sortAsc = key === 'rank'; }
  renderTable();
}
