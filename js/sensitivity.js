// ─── Sensitivity Analysis ─────────────────────────────────────────────────────
// Builds a matrix of Levered IRR values by varying:
//   X-axis: Exit Cap Rate (current ± steps)
//   Y-axis: Hold Period (3 to 10 years)
//
// This answers: "If the market softens and I need to sell earlier or at a worse
// cap rate, does this deal still hit my return threshold?"

function calcIRRForScenario(inp, exitCap, holdPeriod) {
  const scenarioInp = Object.assign({}, inp, { exitCap, hold: holdPeriod });
  const { irrCFs } = buildRows(scenarioInp);
  return calcIRR(irrCFs);
}

function irrColorClass(irr) {
  if (irr === null || irr === undefined) return 'irr-na';
  if (irr >= 0.15) return 'irr-deep-green';
  if (irr >= 0.12) return 'irr-green';
  if (irr >= 0.08) return 'irr-amber';
  if (irr >= 0.05) return 'irr-orange';
  return 'irr-red';
}

function renderSensitivityTable(inp) {
  const placeholder = document.getElementById('sensitivity-placeholder');
  if (!placeholder) return;

  // Build exit cap columns: current ± 0.75% in 0.25% steps (7 columns)
  const step = 0.0025;
  const capCols = [-3, -2, -1, 0, 1, 2, 3].map(n => +(inp.exitCap + n * step).toFixed(4));

  // Hold period rows: 3 through 10 (or up to 10)
  const holdRows = [3, 4, 5, 6, 7, 8, 9, 10].filter(h => h >= 1);

  // Build the IRR matrix
  const matrix = holdRows.map(hold =>
    capCols.map(cap => calcIRRForScenario(inp, cap, hold))
  );

  // Build header row
  const headerCells = capCols.map(cap => {
    const pct = (cap * 100).toFixed(2) + '%';
    const isCurrent = Math.abs(cap - inp.exitCap) < 0.0001;
    return `<th${isCurrent ? ' style="color:var(--gold)"' : ''}>${pct}</th>`;
  }).join('');

  // Build data rows
  const dataRows = holdRows.map((hold, ri) => {
    const cells = capCols.map((cap, ci) => {
      const irr = matrix[ri][ci];
      const cls = irrColorClass(irr);
      const isCurrentCell = Math.abs(cap - inp.exitCap) < 0.0001 && hold === inp.hold;
      const display = irr !== null ? (irr * 100).toFixed(1) + '%' : 'N/A';
      return `<td class="${cls}${isCurrentCell ? ' current-cell' : ''}">${display}</td>`;
    }).join('');
    return `<tr>
      <td class="hold-label">${hold}yr Hold</td>
      ${cells}
    </tr>`;
  }).join('');

  placeholder.innerHTML = `
    <div class="sensitivity-card anim anim-2">
      <div class="sensitivity-head">
        <span class="sensitivity-title">Sensitivity Analysis — Levered IRR</span>
        <span class="sensitivity-desc">Exit Cap Rate (columns) × Hold Period (rows)</span>
      </div>
      <div class="sensitivity-scroll">
        <table class="sensitivity-table">
          <thead>
            <tr>
              <th class="row-header">Hold Period</th>
              ${headerCells}
            </tr>
          </thead>
          <tbody>${dataRows}</tbody>
        </table>
      </div>
      <div style="padding:8px 16px 10px; font-family:var(--mono); font-size:9px; color:var(--text-3); border-top:1px solid var(--border);">
        Gold border = current scenario &nbsp;·&nbsp;
        <span style="color:#6ee09a">■</span> ≥15% &nbsp;
        <span style="color:var(--emerald)">■</span> 12–15% &nbsp;
        <span style="color:var(--amber)">■</span> 8–12% &nbsp;
        <span style="color:#e08050">■</span> 5–8% &nbsp;
        <span style="color:var(--crimson)">■</span> &lt;5%
      </div>
    </div>`;
}
