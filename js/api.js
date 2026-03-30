// ─── API Integration ──────────────────────────────────────────────────────────
// Fetches the live 10-year US Treasury rate from FRED.
// If successful, updates TREASURY and rebuilds the scoring model.
// BLS and Census are marked as future enhancements (data stays hardcoded).

async function fetchFredTreasury(apiKey) {
  const url = `https://api.stlouisfed.org/fred/series/observations` +
    `?series_id=DGS10&sort_order=desc&limit=1&api_key=${apiKey}&file_type=json`;
  try {
    const res  = await fetch(url);
    if (!res.ok) throw new Error(`FRED HTTP ${res.status}`);
    const data = await res.json();
    const obs  = data.observations && data.observations[0];
    if (!obs || obs.value === '.') throw new Error('No observation');
    const rate = parseFloat(obs.value) / 100;
    if (isNaN(rate)) throw new Error('Bad value');
    return rate;
  } catch (err) {
    console.warn('[FRED] fetch failed:', err.message);
    return null;
  }
}

async function initAPI() {
  const fredKey = localStorage.getItem('FRED_API_KEY');

  if (fredKey) {
    const rate = await fetchFredTreasury(fredKey);
    if (rate !== null) {
      TREASURY = rate;
      rebuildMarkets(); // rebuilds scoring + re-renders table/chart/cards
      setSourceDot(0, true, `Treasury (FRED ${(rate*100).toFixed(2)}%)`);
      // Also update the metric card label to show it's live
      const srcEl = document.getElementById('mc-treasury-src');
      if (srcEl) srcEl.textContent = 'Live via FRED';
    } else {
      setSourceDot(0, false, 'Treasury Rate (CSV)');
    }
  } else {
    setSourceDot(0, false, 'Treasury Rate (CSV)');
  }

  // BLS and Census: future enhancement — keep CSV fallback
  setSourceDot(1, false, 'Employment (CSV)');
  setSourceDot(2, false, 'Population (CSV)');
  setSourceDot(3, false, 'Vacancy / Cap Rate');
}

function setSourceDot(index, live, label) {
  const dots = document.querySelectorAll('.source-dot');
  const rows = document.querySelectorAll('.source-row');
  if (!dots[index]) return;

  dots[index].className = 'source-dot ' + (live ? 'live' : 'fallback');
  const textNode = [...rows[index].childNodes].find(n => n.nodeType === 3);
  if (textNode) textNode.textContent = label;
}
