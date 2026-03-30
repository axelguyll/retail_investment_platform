// ─── PDF Export ───────────────────────────────────────────────────────────────
// Generates a clean institutional-white pro forma PDF using jsPDF + AutoTable.
// Layout: header banner → deal summary → sources & uses → return metrics →
//         cash flow table → sensitivity analysis → footer disclaimer

function exportPDF() {
  if (!lastUWInputs || !lastUWRows.length) return;

  const inp  = lastUWInputs;
  const rows = lastUWRows;

  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({ orientation: 'portrait', unit: 'pt', format: 'letter' });

  const pageW  = doc.internal.pageSize.getWidth();
  const pageH  = doc.internal.pageSize.getHeight();
  const margin = 40;
  const usable = pageW - margin * 2;
  let y = margin;

  // Color palette
  const NAVY   = [26, 58, 92];
  const MID    = [45, 106, 159];
  const LIGHT  = [232, 240, 248];
  const GOLD   = [200, 169, 81];
  const GRAY   = [245, 245, 245];
  const MGRAY  = [204, 204, 204];
  const BLACK  = [26, 26, 46];

  const fmt$ = v => {
    if (Math.abs(v) >= 1e6) return '$' + (v/1e6).toFixed(2) + 'M';
    return v.toLocaleString('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0});
  };
  const fmtPct = v => (v * 100).toFixed(2) + '%';
  const today  = new Date().toLocaleDateString('en-US',{month:'long',day:'numeric',year:'numeric'});

  // ── Header Banner ────────────────────────────────────────────────
  doc.setFillColor(...NAVY);
  doc.rect(margin, y, usable, 62, 'F');

  doc.setFont('helvetica','bold');
  doc.setFontSize(14);
  doc.setTextColor(255,255,255);
  doc.text('RETAIL REAL ESTATE PRO FORMA', pageW/2, y + 20, { align:'center' });

  doc.setFont('helvetica','normal');
  doc.setFontSize(9.5);
  doc.setTextColor(...GOLD);
  doc.text(`${inp.name}  ·  ${inp.market}`, pageW/2, y + 36, { align:'center' });

  doc.setFontSize(8);
  doc.setTextColor(180, 190, 210);
  doc.text(`Prepared ${today}`, pageW/2, y + 50, { align:'center' });
  y += 78;

  // ── Section Header helper ────────────────────────────────────────
  function sectionHeader(title) {
    doc.setFillColor(...MID);
    doc.rect(margin, y, usable, 18, 'F');
    doc.setFont('helvetica','bold');
    doc.setFontSize(8);
    doc.setTextColor(255,255,255);
    doc.text(title.toUpperCase(), margin + 8, y + 12);
    y += 24;
  }

  // ── KV Table helper ─────────────────────────────────────────────
  function kvTable(pairs) {
    const colW = usable / 4;
    const rowH = 18;
    const rows2col = [];
    for (let i = 0; i < pairs.length; i += 2) {
      rows2col.push(pairs.slice(i, i+2));
    }
    rows2col.forEach((rowPairs, ri) => {
      const bg = ri % 2 === 0 ? [255,255,255] : GRAY;
      doc.setFillColor(...bg);
      doc.rect(margin, y, usable, rowH, 'F');
      doc.setDrawColor(...MGRAY);
      doc.setLineWidth(0.25);
      doc.rect(margin, y, usable, rowH, 'S');

      rowPairs.forEach((pair, pi) => {
        const x = margin + pi * colW * 2;
        doc.setFont('helvetica','bold');
        doc.setFontSize(8);
        doc.setTextColor(...BLACK);
        doc.text(pair[0], x + 6, y + 12);
        doc.setFont('helvetica','normal');
        doc.text(pair[1], x + colW * 2 - 6, y + 12, { align:'right' });
      });
      y += rowH;
    });
    y += 10;
  }

  // ─── 1. Deal Summary ────────────────────────────────────────────
  sectionHeader('1. Deal Summary');
  const loan   = inp.price * inp.ltv;
  const equity = inp.price - loan;
  kvTable([
    ['Property Name', inp.name],
    ['Market', inp.market],
    ['Square Footage', inp.sqft.toLocaleString() + ' SF'],
    ['Price per SF', fmt$(inp.price / inp.sqft)],
    ['Purchase Price', fmt$(inp.price)],
    ['Year 1 NOI', fmt$(inp.noi)],
    ['Going-In Cap Rate', fmtPct(inp.capRate)],
    ['NOI Growth Rate', fmtPct(inp.noiGrow)],
    ['Vacancy Rate', fmtPct(inp.vac)],
    ['Exit Cap Rate', fmtPct(inp.exitCap)],
    ['Hold Period', inp.hold + ' Years'],
    ['Amortization', inp.amort + ' Years'],
  ]);

  // ─── 2. Sources & Uses ──────────────────────────────────────────
  sectionHeader('2. Sources & Uses');
  const [ads, mo] = debtService(loan, inp.rate, inp.amort);
  kvTable([
    ['Purchase Price', fmt$(inp.price)],
    ['Equity Invested', fmt$(equity)],
    ['Loan Amount', fmt$(loan)],
    ['Loan-to-Value', fmtPct(inp.ltv)],
    ['Interest Rate', fmtPct(inp.rate)],
    ['Monthly Payment', fmt$(mo)],
    ['Annual Debt Service', fmt$(ads)],
    ['DSCR (Year 1)', (inp.noi / ads).toFixed(2) + 'x'],
  ]);

  // ─── 3. Return Metrics ──────────────────────────────────────────
  sectionHeader('3. Return Metrics');

  const { irrCFs } = buildRows(inp);
  const irr  = calcIRR(irrCFs);
  const coc  = rows[0].cfOps / equity;
  const totD = rows.reduce((s,r)=>s+r.totalCF, 0);
  const em   = totD / equity;
  const dscr = ads > 0 ? inp.noi / ads : 0;
  const netS = rows[rows.length-1].saleP;

  // 4-box highlight row
  const metrics = [
    { label:'Levered IRR',       value: irr !== null ? fmtPct(irr) : 'N/A' },
    { label:'Equity Multiple',   value: em.toFixed(2) + 'x' },
    { label:'Cash-on-Cash Yr 1', value: fmtPct(coc) },
    { label:'DSCR (Year 1)',     value: dscr.toFixed(2) + 'x' },
  ];
  const boxW = usable / 4;
  const boxH = 42;
  metrics.forEach((m, i) => {
    const bx = margin + i * boxW;
    doc.setFillColor(...LIGHT);
    doc.setDrawColor(...MGRAY);
    doc.setLineWidth(0.25);
    doc.rect(bx, y, boxW, boxH, 'FD');
    doc.setFont('helvetica','bold');
    doc.setFontSize(16);
    doc.setTextColor(...NAVY);
    doc.text(m.value, bx + boxW/2, y + 24, { align:'center' });
    doc.setFont('helvetica','normal');
    doc.setFontSize(7);
    doc.setTextColor(100,120,150);
    doc.text(m.label.toUpperCase(), bx + boxW/2, y + 36, { align:'center' });
  });
  y += boxH + 12;

  kvTable([
    ['Equity Invested', fmt$(equity)],
    ['Net Sale Proceeds', fmt$(netS)],
    ['Total Distributions', fmt$(totD)],
    ['Year 1 Cash Flow', fmt$(rows[0].cfOps)],
  ]);

  // ─── 4. Cash Flow Projection ────────────────────────────────────
  // Check if we need a new page
  if (y > pageH - 200) { doc.addPage(); y = margin; }

  sectionHeader('4. Cash Flow Projection');

  const cfHead = [['Yr','NOI','Debt Svc','CF (Ops)','Sale Proc.','Total CF','Loan Balance']];
  const cfBody = rows.map(r => [
    r.yr + (r.yr === inp.hold ? ' ★' : ''),
    fmt$(r.noi),
    fmt$(r.ads),
    fmt$(r.cfOps),
    r.saleP ? fmt$(r.saleP) : '—',
    fmt$(r.totalCF),
    fmt$(r.bal),
  ]);

  doc.autoTable({
    startY: y,
    head: cfHead,
    body: cfBody,
    margin: { left: margin, right: margin },
    styles: { font:'helvetica', fontSize:8, cellPadding:4, textColor:BLACK },
    headStyles: { fillColor:NAVY, textColor:[255,255,255], fontStyle:'bold', fontSize:7.5, halign:'center' },
    columnStyles: {
      0: { halign:'center', cellWidth:28 },
      1: { halign:'right' }, 2: { halign:'right' }, 3: { halign:'right' },
      4: { halign:'right' }, 5: { halign:'right', fontStyle:'bold' }, 6: { halign:'right' },
    },
    alternateRowStyles: { fillColor:GRAY },
    didParseCell: (data) => {
      if (data.section === 'body' && data.row.index === rows.length - 1) {
        data.cell.styles.fillColor = LIGHT;
        data.cell.styles.fontStyle = 'bold';
      }
    },
    tableLineColor: MGRAY,
    tableLineWidth: 0.25,
  });

  y = doc.lastAutoTable.finalY + 16;

  // ─── 5. Sensitivity Analysis ────────────────────────────────────
  if (y > pageH - 180) { doc.addPage(); y = margin; }

  sectionHeader('5. Sensitivity Analysis — Levered IRR');

  // Sub-label
  doc.setFont('helvetica','normal');
  doc.setFontSize(7.5);
  doc.setTextColor(100,120,150);
  doc.text('Exit Cap Rate (columns)  ×  Hold Period (rows)  ·  Gold border = current scenario', margin, y);
  y += 12;

  const step = 0.0025;
  const capCols = [-3,-2,-1,0,1,2,3].map(n => +(inp.exitCap + n*step).toFixed(4));
  const holdRows = [3,4,5,6,7,8,9,10];

  const sensHead = [['Hold', ...capCols.map(c => (c*100).toFixed(2)+'%')]];
  const sensBody = holdRows.map(hold =>
    [hold + 'yr', ...capCols.map(cap => {
      const irr2 = calcIRRForScenario(inp, cap, hold);
      return irr2 !== null ? (irr2*100).toFixed(1)+'%' : 'N/A';
    })]
  );

  doc.autoTable({
    startY: y,
    head: sensHead,
    body: sensBody,
    margin: { left: margin, right: margin },
    styles: { font:'helvetica', fontSize:8, cellPadding:3.5, halign:'center', textColor:BLACK },
    headStyles: { fillColor:NAVY, textColor:[255,255,255], fontStyle:'bold', fontSize:7.5, halign:'center' },
    columnStyles: { 0: { halign:'left', cellWidth:38, fontStyle:'bold' } },
    alternateRowStyles: { fillColor:GRAY },
    didParseCell: (data) => {
      if (data.section !== 'body') return;
      const colIdx = data.column.index - 1; // offset for hold label column
      const hold   = holdRows[data.row.index];
      const cap    = capCols[colIdx];
      const irr2   = matrix_irr(inp, cap, hold);
      if (irr2 === null) return;

      // Color fill by IRR threshold
      if (irr2 >= 0.15)       data.cell.styles.fillColor = [34,100,60];
      else if (irr2 >= 0.12)  data.cell.styles.fillColor = [40,110,85];
      else if (irr2 >= 0.08)  data.cell.styles.fillColor = [140,80,30];
      else if (irr2 >= 0.05)  data.cell.styles.fillColor = [160,60,30];
      else                    data.cell.styles.fillColor = [140,40,40];

      if (irr2 >= 0.08) data.cell.styles.textColor = [240,255,240];
      else              data.cell.styles.textColor = [255,220,210];

      // Gold border on current cell
      if (Math.abs(cap - inp.exitCap) < 0.0001 && hold === inp.hold) {
        data.cell.styles.lineColor = GOLD;
        data.cell.styles.lineWidth = 1.5;
        data.cell.styles.fontStyle = 'bold';
      }
    },
    tableLineColor: MGRAY,
    tableLineWidth: 0.25,
  });

  y = doc.lastAutoTable.finalY + 20;

  // ─── Footer ─────────────────────────────────────────────────────
  if (y > pageH - 40) { doc.addPage(); y = margin; }
  doc.setDrawColor(...MGRAY);
  doc.setLineWidth(0.5);
  doc.line(margin, y, margin + usable, y);
  y += 8;
  doc.setFont('helvetica','normal');
  doc.setFontSize(6.5);
  doc.setTextColor(150,150,150);
  doc.text(
    'This pro forma is for illustrative purposes only. All projections are estimates and not guarantees of future performance. ' +
    `Generated by The Ledger · ${today}`,
    pageW/2, y, { align:'center', maxWidth: usable }
  );

  // ─── Save ───────────────────────────────────────────────────────
  const dateStr = new Date().toISOString().slice(0,10);
  const safeName = inp.name.replace(/[^a-z0-9]/gi,'_').replace(/_+/g,'_');
  doc.save(`${safeName}_ProForma_${dateStr}.pdf`);
}

// Helper used by didParseCell (avoids recalculating full matrix inside the hook)
function matrix_irr(inp, cap, hold) {
  if (cap === undefined || cap === null || isNaN(cap)) return null;
  return calcIRRForScenario(inp, cap, hold);
}
