// ─── Chart Config ─────────────────────────────────────────────────────────────
const CHART_TOOLTIP = {
  backgroundColor:'#131626', borderColor:'#1e2138', borderWidth:1,
  titleColor:'#c9a55a', bodyColor:'#dedad0',
  titleFont:{family:"'JetBrains Mono', monospace", size:11},
  bodyFont:{family:"'JetBrains Mono', monospace", size:11},
  padding: 10,
};
const TICK_STYLE = { color:'#464d66', font:{family:"'JetBrains Mono', monospace", size:9} };
const GRID_COLOR = 'rgba(30,33,56,0.9)';

let top10Chart, breakdownChart, scatterChart;

// ─── Market Screener Charts ───────────────────────────────────────────────────

function renderTop10() {
  const d = MARKETS.slice(0,10);
  const ctx = document.getElementById('chart-top10').getContext('2d');
  if (top10Chart) top10Chart.destroy();
  top10Chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: d.map(r=>r.metro),
      datasets: [{
        data: d.map(r=>r.total_score),
        backgroundColor: d.map((_,i) => `rgba(201,165,90,${1 - i*0.07})`),
        borderRadius: 3, borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display:false },
        tooltip: { ...CHART_TOOLTIP, callbacks:{ label: c=>`Score: ${c.parsed.y.toFixed(1)}` } }
      },
      scales: {
        x: { ticks:{...TICK_STYLE, maxRotation:28}, grid:{display:false}, border:{color:GRID_COLOR} },
        y: { min:0, max:105, ticks:TICK_STYLE, grid:{color:GRID_COLOR}, border:{display:false} }
      }
    }
  });
}

function selectMetro(metro) {
  selectedMetro = metro;
  renderTable();
  const r = MARKETS.find(m => m.metro === metro);
  if (!r) return;

  document.getElementById('dd-title').textContent = `${r.metro}, ${r.state}`;
  document.getElementById('drilldown').classList.add('visible');

  const dms = [
    ['Overall Score', r.total_score.toFixed(1), '/ 100', ''],
    ['Rank', `#${r.rank}`, `of ${MARKETS.length}`, ''],
    ['Cap Rate', `${r.cap_rate.toFixed(2)}%`, `+${r.cap_rate_spread.toFixed(2)}% spread`, 'pos'],
    ['Emp. Growth', `${r.employment_growth>0?'+':''}${r.employment_growth.toFixed(2)}%`, 'Annual', r.employment_growth>0?'pos':'neg'],
    ['Pop. Growth', `${r.population_growth>0?'+':''}${r.population_growth.toFixed(2)}%`, 'Annual', r.population_growth>0?'pos':'neg'],
  ];
  document.getElementById('dd-metrics').innerHTML = dms.map(([l,v,s,c])=>`
    <div class="dm-card">
      <div class="dm-label">${l}</div>
      <div class="dm-value" style="color:${c==='pos'?'var(--emerald)':c==='neg'?'var(--crimson)':'var(--text)'}">${v}</div>
      <div class="dm-sub">${s}</div>
    </div>`).join('');

  renderBreakdown(r);
  renderScatter(r);
  setTimeout(() => document.getElementById('drilldown').scrollIntoView({behavior:'smooth',block:'nearest'}), 50);
}

function renderBreakdown(r) {
  const ctx = document.getElementById('chart-breakdown').getContext('2d');
  if (breakdownChart) breakdownChart.destroy();
  breakdownChart = new Chart(ctx, {
    type:'bar',
    data:{
      labels:['Employment (25%)','Population (20%)','Vacancy (25%)','Cap Rate (30%)'],
      datasets:[{
        data:[ r.s_eg*W.eg, r.s_pg*W.pg, r.s_vt*W.vt, r.s_cs*W.cs ],
        backgroundColor:['rgba(201,165,90,0.75)','rgba(56,160,116,0.75)','rgba(212,120,64,0.75)','rgba(201,165,90,0.95)'],
        borderRadius:3, borderSkipped:false,
      }]
    },
    options:{
      responsive:true,
      plugins:{ legend:{display:false}, tooltip:{...CHART_TOOLTIP, callbacks:{label:c=>`Contribution: ${c.parsed.y.toFixed(1)}`}} },
      scales:{
        x:{ ticks:{...TICK_STYLE, maxRotation:20}, grid:{display:false}, border:{color:GRID_COLOR} },
        y:{ min:0, max:32, ticks:TICK_STYLE, grid:{color:GRID_COLOR}, border:{display:false} }
      }
    }
  });
}

function renderScatter(selected) {
  const ctx = document.getElementById('chart-scatter').getContext('2d');
  if (scatterChart) scatterChart.destroy();
  scatterChart = new Chart(ctx, {
    type:'scatter',
    data:{
      datasets:[
        {
          label:'All Markets',
          data: MARKETS.filter(r=>r.metro!==selected.metro).map(r=>({x:r.employment_growth, y:r.cap_rate_spread, metro:r.metro})),
          backgroundColor:'rgba(70,77,102,0.55)', pointRadius:5, pointHoverRadius:7,
        },
        {
          label: selected.metro,
          data:[{x:selected.employment_growth, y:selected.cap_rate_spread}],
          backgroundColor:'rgba(201,165,90,0.95)', pointRadius:10, pointStyle:'star', pointHoverRadius:13,
        }
      ]
    },
    options:{
      responsive:true,
      plugins:{
        legend:{display:false},
        tooltip:{...CHART_TOOLTIP, callbacks:{ label: c => `${c.raw.metro||selected.metro} — Emp: ${c.raw.x.toFixed(2)}%, Spread: +${c.raw.y.toFixed(2)}%` }}
      },
      scales:{
        x:{ title:{display:true,text:'Employment Growth (%)',color:'#464d66',font:{size:9}}, ticks:TICK_STYLE, grid:{color:GRID_COLOR}, border:{display:false} },
        y:{ title:{display:true,text:'Cap Rate Spread (%)',color:'#464d66',font:{size:9}}, ticks:TICK_STYLE, grid:{color:GRID_COLOR}, border:{display:false} }
      }
    }
  });
}
