// ─── Underwriting Math ────────────────────────────────────────────────────────

// Stored after each run — used by sensitivity.js and pdf.js
let lastUWInputs = null;
let lastUWRows   = [];

function debtService(loan, rate, amortYrs) {
  if (!rate || !amortYrs || !loan) return [0,0];
  const r = rate/12, n = amortYrs*12;
  const mo = loan * (r * Math.pow(1+r,n)) / (Math.pow(1+r,n)-1);
  return [+(mo*12).toFixed(2), +mo.toFixed(2)];
}

function remainBal(loan, rate, amortYrs, yrs) {
  if (!rate || !loan) return loan;
  const r = rate/12, n = amortYrs*12, k = yrs*12;
  if (n===k) return 0;
  return Math.max(loan * ((Math.pow(1+r,n)-Math.pow(1+r,k)) / (Math.pow(1+r,n)-1)), 0);
}

function calcIRR(cfs, maxIter=300, tol=1e-9) {
  for (const init of [0.1, 0.15, 0.05, 0.2, 0.25, 0.3, -0.05]) {
    let r = init;
    for (let i=0; i<maxIter; i++) {
      let npv=0, dnpv=0;
      for (let t=0; t<cfs.length; t++) {
        const disc = Math.pow(1+r, t);
        npv  += cfs[t]/disc;
        dnpv -= t*cfs[t]/(disc*(1+r));
      }
      if (Math.abs(dnpv) < 1e-14) break;
      const nr = r - npv/dnpv;
      if (Math.abs(nr-r) < tol && isFinite(nr) && nr > -1) return nr;
      r = nr;
    }
    if (isFinite(r) && r > -1 && r < 10) return r;
  }
  return null;
}

// Build cash flow rows for given inputs (used by runUW and sensitivity grid)
function buildRows(inp) {
  const loan = inp.price * inp.ltv;
  const equity = inp.price - loan;
  const [ads, mo] = debtService(loan, inp.rate, inp.amort);
  const rows = [];
  let cum = 0;
  const irrCFs = [-equity];

  for (let yr=1; yr<=inp.hold; yr++) {
    const noi   = inp.noi * Math.pow(1+inp.noiGrow, yr-1);
    const cfOps = noi - ads;
    const bal   = remainBal(loan, inp.rate, inp.amort, yr);
    let saleP = 0, totalCF = cfOps;
    if (yr === inp.hold) {
      const exitVal = noi / inp.exitCap;
      saleP   = exitVal - bal;
      totalCF = cfOps + saleP;
    }
    cum += totalCF;
    irrCFs.push(totalCF);
    rows.push({ yr, noi, cfOps, saleP, totalCF, cum, bal, ads, mo });
  }
  return { rows, irrCFs, equity, loan, ads, mo };
}

let uwCharts = {};

function runUW() {
  const g = id => parseFloat(document.getElementById(id).value);
  const s = id => document.getElementById(id).value;

  const inp = {
    name:     s('f-name'),
    market:   s('f-market'),
    sqft:     g('f-sqft'),
    price:    g('f-price'),
    noi:      g('f-noi'),
    capRate:  g('f-cap')/100,
    vac:      g('f-vac')/100,
    ltv:      g('f-ltv')/100,
    rate:     g('f-rate')/100,
    amort:    parseInt(document.getElementById('f-amort').value),
    hold:     parseInt(document.getElementById('f-hold').value),
    exitCap:  g('f-exit')/100,
    noiGrow:  g('f-noigrowth')/100,
  };

  const { rows, irrCFs, equity, loan, ads, mo } = buildRows(inp);

  const irr  = calcIRR(irrCFs);
  const dscr = ads>0 ? inp.noi/ads : 0;
  const coc  = equity>0 ? rows[0].cfOps/equity : 0;
  const totD = rows.reduce((s,r)=>s+r.totalCF, 0);
  const em   = equity>0 ? totD/equity : 0;
  const netS = rows[rows.length-1].saleP;

  // Store for sensitivity and PDF use
  lastUWInputs = inp;
  lastUWRows   = rows;

  const cc = (v, good, warn) => v >= good ? 'c-good' : v >= warn ? 'c-warn' : 'c-bad';
  const irrC = irr===null ? 'c-warn' : cc(irr, 0.12, 0.08);
  const emC  = cc(em, 1.8, 1.3);
  const cocC = cc(coc, 0.07, 0.04);
  const dscrC= cc(dscr, 1.25, 1.10);

  const $f = n => n.toLocaleString('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0});
  const pct = n => (n*100).toFixed(2)+'%';

  Object.values(uwCharts).forEach(c=>c&&c.destroy&&c.destroy());
  uwCharts = {};

  document.getElementById('uw-results').innerHTML = `
    <div class="return-grid anim">
      <div class="rm-card highlight ${irrC}">
        <div class="rm-label">Levered IRR</div>
        <div class="rm-value">${irr!==null ? pct(irr) : 'N/A'}</div>
        <div class="rm-sub">${inp.hold}-Year Hold</div>
      </div>
      <div class="rm-card ${emC}">
        <div class="rm-label">Equity Multiple</div>
        <div class="rm-value">${em.toFixed(2)}x</div>
        <div class="rm-sub">Distributions / Equity</div>
      </div>
      <div class="rm-card ${cocC}">
        <div class="rm-label">Cash-on-Cash (Yr 1)</div>
        <div class="rm-value">${pct(coc)}</div>
        <div class="rm-sub">Year 1 CF / Equity</div>
      </div>
      <div class="rm-card ${dscrC}">
        <div class="rm-label">DSCR (Year 1)</div>
        <div class="rm-value">${dscr.toFixed(2)}x</div>
        <div class="rm-sub">NOI / Debt Service</div>
      </div>
    </div>

    <div class="secondary-grid anim anim-1">
      <div class="sg-item">
        <div class="sg-label">Equity Invested</div>
        <div class="sg-value">${$f(equity)}</div>
        <div class="sg-sub">LTV ${(inp.ltv*100).toFixed(0)}%</div>
      </div>
      <div class="sg-item">
        <div class="sg-label">Loan Amount</div>
        <div class="sg-value">${$f(loan)}</div>
        <div class="sg-sub">Rate ${(inp.rate*100).toFixed(2)}%</div>
      </div>
      <div class="sg-item">
        <div class="sg-label">Annual Debt Service</div>
        <div class="sg-value">${$f(ads)}</div>
        <div class="sg-sub">Monthly ${$f(mo)}</div>
      </div>
      <div class="sg-item">
        <div class="sg-label">Net Sale Proceeds</div>
        <div class="sg-value">${$f(netS)}</div>
        <div class="sg-sub">Exit Cap ${(inp.exitCap*100).toFixed(1)}%</div>
      </div>
    </div>

    <div class="cf-wrap anim anim-2">
      <div class="cf-wrap-head">
        <span class="cf-wrap-title">10-Year Cash Flow Projection</span>
      </div>
      <div class="cf-scroll">
        <table>
          <thead><tr>
            <th>Yr</th><th>NOI</th><th>Debt Svc</th><th>CF (Ops)</th>
            <th>Sale Proceeds</th><th>Total CF</th><th>Cumulative CF</th><th>Loan Balance</th>
          </tr></thead>
          <tbody>${rows.map(r=>`<tr class="${r.yr===inp.hold?'row-exit':''}">
            <td>${r.yr}${r.yr===inp.hold?' ★':''}</td>
            <td>${$f(r.noi)}</td>
            <td>${$f(r.ads)}</td>
            <td style="color:${r.cfOps>=0?'var(--emerald)':'var(--crimson)'}">${$f(r.cfOps)}</td>
            <td>${r.saleP?$f(r.saleP):'—'}</td>
            <td style="font-weight:500">${$f(r.totalCF)}</td>
            <td style="color:${r.cum>=0?'var(--emerald)':'var(--crimson)'}">${$f(r.cum)}</td>
            <td style="color:var(--text-3)">${$f(r.bal)}</td>
          </tr>`).join('')}</tbody>
        </table>
      </div>
    </div>

    <div id="sensitivity-placeholder"></div>

    <div class="uw-charts-grid anim anim-3">
      <div class="chart-card" style="margin:0">
        <div class="chart-label">NOI &amp; Operating Cash Flow</div>
        <canvas id="uw-chart-cf" height="200"></canvas>
      </div>
      <div class="chart-card" style="margin:0">
        <div class="chart-label">Cumulative Cash Flow</div>
        <canvas id="uw-chart-cum" height="200"></canvas>
      </div>
    </div>
    <div class="chart-card anim anim-4">
      <div class="chart-label">Loan Balance Over Hold Period</div>
      <canvas id="uw-chart-loan" height="110"></canvas>
    </div>

    <div class="pdf-export-bar anim anim-5">
      <button class="btn-export-pdf" onclick="exportPDF()">
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M4 1h6l3 3v10a1 1 0 01-1 1H4a1 1 0 01-1-1V2a1 1 0 011-1z"/>
          <polyline points="9,1 9,4 12,4"/>
          <line x1="8" y1="7" x2="8" y2="12"/>
          <polyline points="5,10 8,13 11,10"/>
        </svg>
        Export Pro Forma PDF
      </button>
    </div>`;

  // Render sensitivity table (pure JS, no canvas)
  renderSensitivityTable(inp);

  setTimeout(() => {
    const labels = rows.map(r=>`Y${r.yr}`);
    const tOpts = { ...CHART_TOOLTIP, callbacks:{ label:c=>`${c.dataset.label}: ${c.parsed.y.toLocaleString('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0})}` } };
    const scOpts = {
      x: { ticks:TICK_STYLE, grid:{display:false}, border:{color:GRID_COLOR} },
      y: { ticks:{...TICK_STYLE, callback:v=>'$'+(Math.abs(v)>=1e6?(v/1e6).toFixed(1)+'M':(v/1e3).toFixed(0)+'k')}, grid:{color:GRID_COLOR}, border:{display:false} }
    };

    uwCharts.cf = new Chart(document.getElementById('uw-chart-cf'), {
      type:'bar',
      data:{
        labels,
        datasets:[
          { label:'NOI', data:rows.map(r=>r.noi), backgroundColor:'rgba(201,165,90,0.7)', borderRadius:3 },
          { label:'Cash Flow', data:rows.map(r=>r.cfOps), backgroundColor:'rgba(56,160,116,0.7)', borderRadius:3 },
        ]
      },
      options:{ responsive:true, plugins:{ legend:{labels:{color:'#8a91aa',font:{size:10,family:"'JetBrains Mono',monospace"}}}, tooltip:tOpts }, scales:scOpts }
    });

    uwCharts.cum = new Chart(document.getElementById('uw-chart-cum'), {
      type:'line',
      data:{
        labels,
        datasets:[{
          label:'Cumulative CF',
          data:rows.map(r=>r.cum),
          borderColor:'rgba(201,165,90,0.8)',
          backgroundColor:'rgba(201,165,90,0.07)',
          fill:true, tension:0.35,
          pointRadius:5, pointBackgroundColor:'rgba(201,165,90,0.9)',
        }]
      },
      options:{ responsive:true, plugins:{ legend:{display:false}, tooltip:tOpts }, scales:scOpts }
    });

    uwCharts.loan = new Chart(document.getElementById('uw-chart-loan'), {
      type:'line',
      data:{
        labels,
        datasets:[{
          label:'Loan Balance',
          data:rows.map(r=>r.bal),
          borderColor:'rgba(100,110,160,0.7)',
          backgroundColor:'rgba(100,110,160,0.07)',
          fill:true, tension:0.35,
          pointRadius:5, pointBackgroundColor:'rgba(100,110,160,0.8)',
        }]
      },
      options:{ responsive:true, plugins:{ legend:{display:false}, tooltip:tOpts }, scales:scOpts }
    });
  }, 60);
}
