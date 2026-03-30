// ─── Market Data ──────────────────────────────────────────────────────────────
// eg = employment growth %, pg = population growth %, vt = vacancy trend pp, cr = cap rate %
const RAW = [
  { metro:"Austin",           state:"TX", eg:3.2,  pg:2.8,  vt:-1.5, cr:6.2 },
  { metro:"Dallas-Fort Worth",state:"TX", eg:2.8,  pg:2.3,  vt:-0.8, cr:6.5 },
  { metro:"Phoenix",          state:"AZ", eg:2.6,  pg:2.1,  vt:-0.6, cr:6.7 },
  { metro:"Nashville",        state:"TN", eg:2.5,  pg:2.0,  vt:-0.9, cr:6.4 },
  { metro:"Charlotte",        state:"NC", eg:2.4,  pg:2.1,  vt:-0.7, cr:6.6 },
  { metro:"Tampa",            state:"FL", eg:2.3,  pg:2.4,  vt:-0.5, cr:6.8 },
  { metro:"Raleigh",          state:"NC", eg:2.2,  pg:1.9,  vt:-0.8, cr:6.5 },
  { metro:"Orlando",          state:"FL", eg:2.1,  pg:2.2,  vt:-0.4, cr:6.9 },
  { metro:"Atlanta",          state:"GA", eg:2.0,  pg:1.7,  vt:-0.6, cr:6.7 },
  { metro:"Salt Lake City",   state:"UT", eg:2.0,  pg:1.5,  vt:-0.4, cr:6.6 },
  { metro:"Jacksonville",     state:"FL", eg:1.9,  pg:1.8,  vt:-0.3, cr:7.0 },
  { metro:"Las Vegas",        state:"NV", eg:1.8,  pg:1.6,  vt:-0.2, cr:7.1 },
  { metro:"San Antonio",      state:"TX", eg:1.8,  pg:1.6,  vt:-0.5, cr:6.9 },
  { metro:"Houston",          state:"TX", eg:1.8,  pg:1.5,  vt: 0.1, cr:7.0 },
  { metro:"Denver",           state:"CO", eg:1.7,  pg:1.4,  vt:-0.2, cr:6.8 },
  { metro:"Indianapolis",     state:"IN", eg:1.6,  pg:1.2,  vt:-0.3, cr:7.2 },
  { metro:"Miami",            state:"FL", eg:1.6,  pg:1.4,  vt: 0.2, cr:6.5 },
  { metro:"Tucson",           state:"AZ", eg:1.4,  pg:1.1,  vt:-0.1, cr:7.3 },
  { metro:"Columbus",         state:"OH", eg:1.5,  pg:1.1,  vt:-0.2, cr:7.1 },
  { metro:"Seattle",          state:"WA", eg:1.4,  pg:1.2,  vt: 0.3, cr:6.2 },
  { metro:"Richmond",         state:"VA", eg:1.2,  pg:0.9,  vt:-0.1, cr:7.0 },
  { metro:"San Diego",        state:"CA", eg:1.3,  pg:0.9,  vt: 0.1, cr:6.0 },
  { metro:"Minneapolis",      state:"MN", eg:1.2,  pg:0.8,  vt: 0.4, cr:7.0 },
  { metro:"Oklahoma City",    state:"OK", eg:1.0,  pg:0.8,  vt: 0.0, cr:7.5 },
  { metro:"Kansas City",      state:"MO", eg:0.9,  pg:0.6,  vt: 0.2, cr:7.3 },
  { metro:"Louisville",       state:"KY", eg:0.9,  pg:0.6,  vt: 0.3, cr:7.4 },
  { metro:"Portland",         state:"OR", eg:1.0,  pg:0.7,  vt: 0.5, cr:6.8 },
  { metro:"Albuquerque",      state:"NM", eg:0.9,  pg:0.5,  vt: 0.2, cr:7.5 },
  { metro:"Memphis",          state:"TN", eg:0.8,  pg:0.4,  vt: 0.5, cr:8.0 },
  { metro:"Los Angeles",      state:"CA", eg:0.8,  pg:0.1,  vt: 0.9, cr:5.8 },
  { metro:"Philadelphia",     state:"PA", eg:0.9,  pg:0.5,  vt: 0.6, cr:7.2 },
  { metro:"Chicago",          state:"IL", eg:0.7,  pg:0.2,  vt: 0.8, cr:7.5 },
  { metro:"Providence",       state:"RI", eg:0.6,  pg:0.2,  vt: 0.4, cr:7.3 },
  { metro:"Hartford",         state:"CT", eg:0.5,  pg:0.1,  vt: 0.7, cr:7.6 },
  { metro:"Detroit",          state:"MI", eg:0.5,  pg:-0.2, vt: 0.9, cr:8.2 },
  { metro:"Milwaukee",        state:"WI", eg:0.4,  pg:-0.1, vt: 0.7, cr:7.6 },
  { metro:"Pittsburgh",       state:"PA", eg:0.4,  pg:-0.3, vt: 1.0, cr:7.8 },
  { metro:"St. Louis",        state:"MO", eg:0.3,  pg:-0.3, vt: 0.8, cr:7.8 },
  { metro:"Cleveland",        state:"OH", eg:0.3,  pg:-0.4, vt: 1.1, cr:8.0 },
  { metro:"Buffalo",          state:"NY", eg:0.4,  pg:-0.2, vt: 0.6, cr:7.9 },
  { metro:"New York-Newark",  state:"NY", eg:0.6,  pg:-0.1, vt: 1.2, cr:5.5 },
  { metro:"San Francisco",    state:"CA", eg:-0.2, pg:-0.5, vt: 2.1, cr:5.5 },
];

// 10-year Treasury rate — updated dynamically via FRED API if key is present
let TREASURY = 4.30;

// Scoring weights
const W = { eg:0.25, pg:0.20, vt:0.25, cs:0.30 };
