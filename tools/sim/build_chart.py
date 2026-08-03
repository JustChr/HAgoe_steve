"""Turn ``peak15_run.json`` into a single self-contained HTML readout.

Nothing here computes anything about charging — it only reshapes the simulation's
quarter-hour records into compact arrays and hands them to the page. Run
``python peak15.py`` first.
"""

from __future__ import annotations

import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent


def build() -> pathlib.Path:
    run = json.load(open(HERE / "peak15_run.json"))
    slots = run["slots"]

    def col(key: str, scale: float = 1.0) -> list[int]:
        return [round(s[key] * scale) for s in slots]

    payload = {
        "meta": run["meta"],
        "baseline": run["baseline"],
        "hold": run["hold"],
        "flat": run["flat"],
        "days": run["days"],
        # Watts as integers; SoC ×10; price ×1000. The page divides back.
        "series": {
            "gridShip": col("grid_w"),
            "gridOff": col("grid_off_w"),
            "gridHold": col("grid_hold_w"),
            "gridFlat": col("grid_flat_w"),
            "socFlat": col("soc_flat", 10),
            "carFlat": col("car_flat_w"),
            "base": col("base_w"),
            "hp": col("hp_w"),
            "car": col("car_w"),
            "sauna": col("sauna_w"),
            "pv": col("pv_w"),
            "batt": col("batt_w"),
            "socShip": col("soc", 10),
            "socOff": col("soc_off", 10),
            "socHold": col("soc_hold", 10),
            "price": col("price", 1000),
            "tier": [{"off": 0, "soft": 1, "hard": 2}[s["tier"]] for s in slots],
        },
        "reasons": [s["reason"] for s in slots],
        "peakReasons": [s["peak_reason"] for s in slots],
    }

    html = TEMPLATE.replace("__DATA__", json.dumps(payload, separators=(",", ":")))
    out = HERE / "peak15_chart.html"
    out.write_text(html, encoding="utf-8")
    return out


TEMPLATE = r"""<title>Peak shaving — 15 winter days against a 4 kW ceiling</title>
<style>
  :root{
    color-scheme: light;
    --ground:#f2f4f3; --panel:#fcfcfb; --raised:#ffffff;
    --ink:#101312; --ink-2:#565a58; --ink-3:#8a8d8a;
    --rule:#e1e0d9; --axis:#c3c2b7; --edge:rgba(16,19,18,.10);
    --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a;
    --l1:#4a3aa7; --l2:#eda100; --l3:#1baf7a; --l4:#e34948;
    --pv:#008300; --crit:#d03b3b; --good:#0ca30c; --warn:#fab219;
    --mono: ui-monospace, "SF Mono", "Cascadia Mono", "Segoe UI Mono", Menlo, monospace;
    --sans: system-ui, -apple-system, "Segoe UI", sans-serif;
  }
  @media (prefers-color-scheme: dark){
    :root:where(:not([data-theme="light"])){
      color-scheme: dark;
      --ground:#0d0f0e; --panel:#1a1a19; --raised:#212220;
      --ink:#ffffff; --ink-2:#c3c2b7; --ink-3:#898781;
      --rule:#2c2c2a; --axis:#383835; --edge:rgba(255,255,255,.10);
      --s1:#3987e5; --s2:#d95926; --s3:#199e70;
      --l1:#9085e9; --l2:#c98500; --l3:#199e70; --l4:#e66767;
      --pv:#008300; --crit:#d03b3b; --good:#0ca30c; --warn:#fab219;
    }
  }
  :root[data-theme="dark"]{
    color-scheme: dark;
    --ground:#0d0f0e; --panel:#1a1a19; --raised:#212220;
    --ink:#ffffff; --ink-2:#c3c2b7; --ink-3:#898781;
    --rule:#2c2c2a; --axis:#383835; --edge:rgba(255,255,255,.10);
    --s1:#3987e5; --s2:#d95926; --s3:#199e70;
    --l1:#9085e9; --l2:#c98500; --l3:#199e70; --l4:#e66767;
    --pv:#008300; --crit:#d03b3b; --good:#0ca30c; --warn:#fab219;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
       font-size:15px;line-height:1.5;-webkit-font-smoothing:antialiased}
  .wrap{max-width:1240px;margin:0 auto;padding:32px 20px 72px;display:flex;
        flex-direction:column;gap:26px}
  .eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.13em;
           text-transform:uppercase;color:var(--ink-3)}
  h1{font-size:clamp(23px,3.1vw,33px);line-height:1.16;margin:6px 0 0;
     font-weight:640;letter-spacing:-.02em;text-wrap:balance;max-width:22ch}
  .lede{color:var(--ink-2);max-width:66ch;margin:10px 0 0}
  .tiles{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(178px,1fr))}
  .tile{background:var(--panel);border:1px solid var(--edge);border-radius:3px;
        padding:14px 16px;display:flex;flex-direction:column;gap:3px}
  .tile .k{font-family:var(--mono);font-size:10.5px;letter-spacing:.1em;
           text-transform:uppercase;color:var(--ink-3)}
  .tile .v{font-size:27px;font-weight:640;letter-spacing:-.02em}
  .tile .u{font-size:14px;font-weight:500;color:var(--ink-2)}
  .tile .n{font-size:12.5px;color:var(--ink-2)}
  .tile.bad .v{color:var(--crit)}
  .tile.good{border-color:color-mix(in oklab,var(--s3) 55%, var(--edge))}
  .tile.good .v{color:var(--s3)}
  .bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;
       background:var(--panel);border:1px solid var(--edge);border-radius:3px;padding:10px 12px}
  .bar .lbl{font-family:var(--mono);font-size:10.5px;letter-spacing:.1em;
            text-transform:uppercase;color:var(--ink-3);margin-right:2px}
  button{font:inherit;font-size:12.5px;font-family:var(--mono);color:var(--ink-2);
         background:transparent;border:1px solid var(--edge);border-radius:2px;
         padding:5px 10px;cursor:pointer}
  button:hover{background:var(--raised);color:var(--ink)}
  button[aria-pressed="true"]{background:var(--ink);color:var(--panel);border-color:var(--ink)}
  button:focus-visible{outline:2px solid var(--s1);outline-offset:2px}
  .plots{background:var(--panel);border:1px solid var(--edge);border-radius:3px;
         padding:6px 4px 4px;position:relative}
  .panel{padding:9px 12px 0}
  .phead{display:flex;justify-content:space-between;align-items:baseline;gap:14px;
         flex-wrap:wrap;margin-bottom:2px}
  .ptitle{font-size:13px;font-weight:620;letter-spacing:-.005em}
  .psub{font-family:var(--mono);font-size:10.5px;color:var(--ink-3)}
  .legend{display:flex;flex-wrap:wrap;gap:11px;align-items:center}
  .lg{display:inline-flex;align-items:center;gap:5px;font-size:11.5px;color:var(--ink-2);
      font-family:var(--mono)}
  .sw{width:11px;height:3px;border-radius:1.5px;flex:none}
  .sw.box{height:9px;width:9px;border-radius:2px}
  svg{display:block;width:100%;overflow:visible}
  .tick{font-family:var(--mono);font-size:9.5px;fill:var(--ink-3)}
  .glab{font-family:var(--mono);font-size:10px;fill:var(--ink-3)}
  .plots{isolation:isolate}
  .tip{position:absolute;pointer-events:none;z-index:50;background:var(--raised);
       border:1px solid var(--axis);border-radius:3px;padding:9px 11px;font-size:12px;
       box-shadow:0 8px 26px rgba(0,0,0,.22);width:226px;opacity:0;transition:opacity .1s}
  .tip .th{font-family:var(--mono);font-size:10.5px;letter-spacing:.07em;
           text-transform:uppercase;color:var(--ink-3);margin-bottom:6px}
  .tip table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
  .tip td{padding:1.5px 0;font-size:11.5px}
  .tip td.n{text-align:right;font-family:var(--mono);padding-left:12px}
  .tip .why{margin-top:7px;padding-top:6px;border-top:1px solid var(--rule);
            color:var(--ink-2);font-size:11px;line-height:1.4}
  .tbl{overflow-x:auto;background:var(--panel);border:1px solid var(--edge);border-radius:3px}
  table.data{border-collapse:collapse;width:100%;font-size:12.5px;
             font-variant-numeric:tabular-nums;font-family:var(--mono)}
  table.data th{text-align:right;font-weight:600;color:var(--ink-3);font-size:10px;
                letter-spacing:.08em;text-transform:uppercase;padding:9px 10px;
                border-bottom:1px solid var(--axis);white-space:nowrap}
  table.data th:first-child,table.data td:first-child{text-align:left}
  table.data td{padding:7px 10px;text-align:right;border-bottom:1px solid var(--rule);
                white-space:nowrap}
  table.data tr:last-child td{border-bottom:none}
  table.data tr.sel td{background:var(--raised)}
  .over{color:var(--crit);font-weight:600}
  .note{color:var(--ink-2);font-size:13.5px;max-width:74ch}
  .note b{color:var(--ink);font-weight:620}
  ol.steps{max-width:70ch;margin:16px 0 0;padding-left:0;list-style:none;counter-reset:s;
           display:flex;flex-direction:column;gap:9px}
  ol.steps li{counter-increment:s;position:relative;padding-left:30px;color:var(--ink-2);
              font-size:14px;line-height:1.5}
  ol.steps li::before{content:counter(s);position:absolute;left:0;top:1px;
      font-family:var(--mono);font-size:10.5px;color:var(--ink-3);
      border:1px solid var(--edge);border-radius:2px;width:19px;height:19px;
      display:grid;place-items:center}
  ol.steps b{color:var(--ink);font-weight:620}
  h2{font-size:17px;font-weight:640;letter-spacing:-.01em;margin:0 0 2px}
  .sec{display:flex;flex-direction:column;gap:11px}
  .foot{color:var(--ink-3);font-size:12px;font-family:var(--mono);line-height:1.65}
  @media (prefers-reduced-motion: reduce){*{transition:none!important}}
</style>

<div class="wrap">
  <header>
    <div class="eyebrow">Closed-loop simulation · goe_steve engine · 1440 quarter-hours</div>
    <h1>Fifteen winter days against a 4 kW ceiling</h1>
    <p class="lede">The real decision engine drives a model house: every quarter-hour it
      reads the grid, decides, and the house reacts to what it decided. Four runs of the
      same fortnight, all driving the engine as it now stands. The ceiling is reachable —
      <b>5 quarter-hours out of 1440 miss it</b>, and they are two cold mornings and one
      evening when the wallbox was driven by hand.</p>

    <ol class="steps">
      <li><b>Cheapest hours first, then any hour.</b> <em>Keep ready for peaks above</em>
        tops the battery up at any price once it drops below the level you set. In December
        the binding constraint is not what energy costs, it is having any stored energy at
        all: PV gives about 1 kWh on a dark day while the house takes 30–58, so the five
        cheap midday hours never keep up — and a pack sitting on its floor shaves nothing.
        It is a floor, not a cap; cheap hours still fill deeper.</li>
      <li><b>Stock up for tonight, and hold what you bought.</b> Fills at any price
        <em>and</em> raises the resting reserve, so the afternoon's ordinary load comes off
        the grid instead of spending the charge before the sauna starts. Filling without
        holding gave the whole stock away by 18:30. On Dec 6 the house pulls 11.8 kW and
        the grid never crosses 4 kW — in every run, including the one with peak protection
        switched off.</li>
      <li><b>Keep defending after the first miss.</b> By default, once a window has
        overshot, holding below the target saves nothing that month — so the guard stands
        down. Against an <em>agreed capacity</em> rather than a monthly demand charge that
        trade is the wrong way round: turn <em>Allow up to this month's peak</em> off. This
        one is a setting, not a code change.</li>
    </ol>
  </header>

  <div class="tiles" id="tiles"></div>

  <div class="bar">
    <span class="lbl">Day</span>
    <button data-day="-1" aria-pressed="true">All 15</button>
    <span id="dayBtns" style="display:contents"></span>
  </div>

  <div class="plots" id="plots">
    <div class="tip" id="tip"></div>
  </div>

  <section class="sec">
    <h2>What the fortnight did, day by day</h2>
    <p class="note">Peak columns are the highest quarter-hour average that day — the unit an
      Austrian capacity tariff actually bills. <b>Uncapped</b> is what the house alone wanted
      before the battery or the wallbox were asked to help.</p>
    <div class="tbl"><table class="data" id="tbl"></table></div>
  </section>

  <section class="sec">
    <h2>What still misses, and why</h2>
    <p class="note"><b>Dec 7, 07:15 and 07:30 — two quarter-hours, up to 5.2 kW.</b>
      The coldest morning (−9 °C). The battery is genuinely empty at 19.7 %: the heat pump
      wants 3.3–4.4 kW for its morning recovery and the overnight car charge has already
      used the headroom that would have refilled the pack. An energy shortage, not a control
      failure — the day needs 72 kWh and a flat 4 kW supplies 96, so there is little slack
      left to buffer with. Trimming the car on the two coldest nights would clear it.</p>
    <p class="note"><b>Dec 13, 18:45–20:30 — three quarter-hours, up to 5.1 kW.</b> The
      sauna evening where the wallbox was in <em>Manual</em>. The battery is at 76 % with
      plenty of energy, but it is pinned at −10.2 kW: its <em>inverter power limit</em>, not
      its charge. Re-run that evening in Smart and the guard pauses the car, the battery
      covers the sauna alone, and all three misses disappear — while the car still collects
      the same energy, just later in the night. The sauna is shavable; charging the car
      through it is not.</p>

    <h2 style="margin-top:12px">What is measured and what is modelled</h2>
    <p class="note"><b>Measured</b> (from the recorder): the household baseline shape (p25 per
      hour of day over 2037 winter hours), the PV days (real December days), the price curve
      (EPEX total price, 0.22–0.42 €/kWh, cheapest around 13:00) and the home battery
      (30.5 kWh usable, 10.2 kW — both derived by regression, not assumed).</p>
    <p class="note"><b>Modelled</b>, because no measurement exists: the heat pump (the Nibe has
      no long-term statistics before Aug 2026) and the car's nightly appetite. The sauna is
      8.7 kW flat out for a 45-minute heat-up and about 4 kW thereafter — roughly 13 kWh an
      evening, once a week, which is how it is actually used. The split is calibrated against
      the one number that is measured: 36.4 kWh/day of house consumption over 106 winter
      days. A 90 % round trip is charged against the battery, which matters here because
      ceiling-fill cycles it far harder than the other runs.</p>
    <p class="note"><b>The chatter, and how wide the fix had to be.</b> Grid charging used
      to stop the moment the battery reached its target and resume the instant it dipped
      below. Five cheap hours a day hides that; a battery kept ready around the clock does
      not — the setpoint flips between "import hard" and "import nothing" every cycle and
      the pack pays a round trip each time. It now waits for the SoC to fall <b>2 %</b>
      below the target before resuming. The width is measured, not picked: against a 100 %
      target the fortnight imported 864 kWh with no band, <b>776 kWh at 2 %</b>, 771 at 5 %
      and 769 at 10 % — so 2 % captures 88 of the 95 kWh available, and it is the widest
      band that costs nothing in peak performance. At 5 % and 10 % the breach count starts
      going back up: a wider band just means arriving at the evening with a flatter
      battery.</p>
    <p class="foot">Ceiling 4.00 kW · soft tier from 3.60 kW · hard tier at 4.20 kW ·
      shipped run: reserve 50 %, shaving floor 35 % (live settings), readiness off ·
      ceiling-fill: keep-ready 95 %, shaving floor 20 %, 2.5 kW over the running load,
      month allowance off · all four runs stock up before the two sauna evenings ·
      the wallbox's cheap-price threshold is 0.26 €/kWh in every run, so the comparison
      isolates the home battery · quarter-hours aligned to the billing window · engine
      ticked every 30 s, recorded every 15 min.</p>
  </section>
</div>

<script>
const D = __DATA__;
const S = D.series, N = S.gridShip.length, SLOTS_PER_DAY = 96;
let day = -1, hoverI = null;

const kw = v => (v/1000);
const f2 = v => v.toFixed(2);

/* ---- stat tiles ------------------------------------------------------------------ */
function tiles(){
  const m=D.meta,b=D.baseline,h=D.hold,fl=D.flat;
  const t=[
    {k:'Worst quarter-hour · off',v:f2(kw(b.billed_peak_w)),u:'kW',n:'no peak protection',bad:true},
    {k:'Worst quarter-hour · shipped',v:f2(kw(m.billed_peak_w)),u:'kW',
     n:'today’s settings'},
    {k:'Worst quarter-hour · ceiling-fill',v:f2(kw(fl.billed_peak_w)),u:'kW',
     n:'two cold mornings, nothing else',good:true},
    {k:'Over 4 kW · ceiling-fill',v:String(fl.breaches),u:'/ '+fl.slots,
     n:'shipped '+m.breaches+' · off '+b.breaches,good:true},
    {k:'Car energy · ceiling-fill',v:String(Math.round(fl.car_kwh)),u:'kWh',
     n:'more than shipped ('+Math.round(m.car_kwh)+' kWh)'},
    {k:'What it costs',v:'+'+Math.round(fl.cost_eur-m.cost_eur),u:'€ / 15 days',
     n:'€'+Math.round(fl.cost_eur)+' vs €'+Math.round(m.cost_eur)+' shipped'},
  ];
  document.getElementById('tiles').innerHTML = t.map(x=>
    `<div class="tile${x.bad?' bad':''}${x.good?' good':''}"><span class="k">${x.k}</span>
     <span class="v">${x.v} <span class="u">${x.u}</span></span>
     <span class="n">${x.n}</span></div>`).join('');
}

/* ---- panel definitions ------------------------------------------------------------ */
const PANELS = [
  { id:'grid', h:168, title:'Grid import', sub:'kW · the quarter-hour average that gets billed',
    kind:'lines', zero:true,
    series:[ {k:'gridOff', c:'var(--s2)', lab:'protection off'},
             {k:'gridShip',c:'var(--s1)', lab:'as shipped'},
             {k:'gridFlat',c:'var(--s3)', lab:'ceiling-fill'} ],
    rules:[ {y:4000,c:'var(--crit)',lab:'4.00 kW ceiling'} ] },
  { id:'load', h:150, title:'Where the power goes', sub:'kW · stacked, as shipped',
    kind:'stack',
    series:[ {k:'base', c:'var(--l1)', lab:'household base'},
             {k:'hp',   c:'var(--l2)', lab:'heat pump'},
             {k:'car',  c:'var(--l3)', lab:'wallbox'},
             {k:'sauna',c:'var(--l4)', lab:'sauna'} ] },
  { id:'soc', h:132, title:'Home battery charge', sub:'% · 30.5 kWh usable',
    kind:'lines', fixed:[0,100],
    series:[ {k:'socOff', c:'var(--s2)', lab:'protection off', sc:10},
             {k:'socShip',c:'var(--s1)', lab:'as shipped', sc:10},
             {k:'socFlat',c:'var(--s3)', lab:'ceiling-fill', sc:10} ],
    rules:[ {y:20,c:'var(--axis)',lab:'20 % ceiling-fill floor',side:'r'},
            {y:35,c:'var(--axis)',lab:'35 % shaving floor'} ] },
  { id:'flow', h:126, title:'Solar and battery power', sub:'kW · battery below zero = discharging',
    kind:'flow' },
  { id:'price', h:96, title:'Electricity price', sub:'€/kWh · EPEX total price',
    kind:'lines', zero:true, solo:true,
    series:[ {k:'price', c:'var(--ink-2)', lab:'price', sc:1000} ] },
];

const PAD = {l:46, r:14, t:6, b:16};

function range(){ return day<0 ? [0,N] : [day*SLOTS_PER_DAY,(day+1)*SLOTS_PER_DAY]; }

function build(){
  const [a,b]=range(), n=b-a;
  const host=document.getElementById('plots');
  [...host.querySelectorAll('.panel')].forEach(e=>e.remove());

  PANELS.forEach((p,pi)=>{
    const el=document.createElement('div');
    el.className='panel'; el.dataset.p=p.id;
    const W=1000, H=p.h, iw=W-PAD.l-PAD.r, ih=H-PAD.t-PAD.b;

    // --- vertical scale
    let lo=0, hi=1;
    if(p.fixed){ [lo,hi]=p.fixed; }
    else if(p.kind==='stack'){
      for(let i=a;i<b;i++){ let s=0; p.series.forEach(q=>s+=S[q.k][i]); hi=Math.max(hi,s); }
      hi=hi/1000;
    } else if(p.kind==='flow'){
      for(let i=a;i<b;i++){ hi=Math.max(hi,S.pv[i],S.batt[i]); lo=Math.min(lo,S.batt[i]); }
      hi/=1000; lo/=1000;
    } else {
      hi=-Infinity;
      p.series.forEach(q=>{ const sc=q.sc||1;
        for(let i=a;i<b;i++) hi=Math.max(hi,S[q.k][i]/sc); });
      if(p.id==='grid') hi=Math.max(hi/1000, 4.4); else hi*=1.12;
    }
    if(p.id==='grid'||p.kind==='stack') hi=Math.ceil(hi);
    const pad=(hi-lo)*0.06; if(!p.fixed && p.kind!=='stack'){ hi+=pad; lo-=lo<0?pad:0; }

    const X = i => PAD.l + (i-a)*iw/(n-1||1);
    const Y = v => PAD.t + ih - (v-lo)/(hi-lo)*ih;

    // --- ticks
    const nT = p.h>140?4:3, ticks=[];
    for(let t=0;t<=nT;t++) ticks.push(lo+(hi-lo)*t/nT);

    let g='';
    ticks.forEach(t=>{ const y=Y(t).toFixed(1);
      g+=`<line x1="${PAD.l}" y1="${y}" x2="${W-PAD.r}" y2="${y}" stroke="var(--rule)" stroke-width="1"/>`;
      g+=`<text class="tick" x="${PAD.l-7}" y="${(+y+3.2).toFixed(1)}" text-anchor="end">${
          Math.abs(hi-lo)<3?t.toFixed(2):t.toFixed(1)}</text>`; });

    // --- day separators / hour ticks
    let xax='';
    if(day<0){
      for(let d=0;d<15;d++){
        const x=X(d*SLOTS_PER_DAY);
        if(d) xax+=`<line x1="${x.toFixed(1)}" y1="${PAD.t}" x2="${x.toFixed(1)}" y2="${PAD.t+ih}" stroke="var(--rule)" stroke-width="1"/>`;
        if(pi===PANELS.length-1) xax+=`<text class="tick" x="${(x+iw/30).toFixed(1)}" y="${H-3}" text-anchor="middle">${d+1}</text>`;
      }
    } else {
      for(let hh=0;hh<=24;hh+=3){
        const x=X(a+Math.min(hh*4,n-1));
        xax+=`<line x1="${x.toFixed(1)}" y1="${PAD.t}" x2="${x.toFixed(1)}" y2="${PAD.t+ih}" stroke="var(--rule)" stroke-width="1"/>`;
        if(pi===PANELS.length-1) xax+=`<text class="tick" x="${x.toFixed(1)}" y="${H-3}" text-anchor="middle">${String(hh).padStart(2,'0')}</text>`;
      }
    }

    // --- marks
    let marks='';
    if(p.kind==='stack'){
      const acc=new Float64Array(n);
      p.series.forEach(q=>{
        let up='',dn='';
        for(let i=a;i<b;i++){ const j=i-a;
          up+=`${j?'L':'M'}${X(i).toFixed(1)},${Y((acc[j]+S[q.k][i])/1000).toFixed(1)}`; }
        for(let i=b-1;i>=a;i--){ const j=i-a;
          dn+=`L${X(i).toFixed(1)},${Y(acc[j]/1000).toFixed(1)}`; }
        marks+=`<path d="${up}${dn}Z" fill="${q.c}" fill-opacity=".82" stroke="var(--panel)" stroke-width="1.2"/>`;
        for(let i=a;i<b;i++) acc[i-a]+=S[q.k][i];
      });
    } else if(p.kind==='flow'){
      let up='';
      for(let i=a;i<b;i++) up+=`${i===a?'M':'L'}${X(i).toFixed(1)},${Y(S.pv[i]/1000).toFixed(1)}`;
      up+=`L${X(b-1).toFixed(1)},${Y(0).toFixed(1)}L${X(a).toFixed(1)},${Y(0).toFixed(1)}Z`;
      marks+=`<path d="${up}" fill="var(--pv)" fill-opacity=".24" stroke="var(--pv)" stroke-width="1.6"/>`;
      let ln='';
      for(let i=a;i<b;i++) ln+=`${i===a?'M':'L'}${X(i).toFixed(1)},${Y(S.batt[i]/1000).toFixed(1)}`;
      marks+=`<line x1="${PAD.l}" y1="${Y(0).toFixed(1)}" x2="${W-PAD.r}" y2="${Y(0).toFixed(1)}" stroke="var(--axis)" stroke-width="1"/>`;
      marks+=`<path d="${ln}" fill="none" stroke="var(--s1)" stroke-width="2" stroke-linejoin="round"/>`;
    } else {
      p.series.forEach(q=>{ const sc=q.sc||1, dv=(p.id==='grid')?1000:1;
        let ln='';
        for(let i=a;i<b;i++) ln+=`${i===a?'M':'L'}${X(i).toFixed(1)},${Y(S[q.k][i]/sc/dv).toFixed(1)}`;
        marks+=`<path d="${ln}" fill="none" stroke="${q.c}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>`;
      });
    }

    // --- threshold rules (solid hairlines). The label sits in the left margin on an
    // opaque plate so it never has to compete with the data for the same pixels.
    let rules='';
    (p.rules||[]).forEach(r=>{ const y=Y(r.y/(p.id==='grid'?1000:1));
      if(y<PAD.t+6||y>PAD.t+ih-2) return;
      rules+=`<line x1="${PAD.l}" y1="${y.toFixed(1)}" x2="${W-PAD.r}" y2="${y.toFixed(1)}" stroke="${r.c}" stroke-width="1.5"/>`;
      const tw=r.lab.length*5.4+8;
      const rx = r.side==='r' ? (W-PAD.r-5-tw) : (PAD.l+5);
      rules+=`<rect x="${rx.toFixed(1)}" y="${(y-12).toFixed(1)}" width="${tw}" height="12" rx="2" fill="var(--panel)"/>`;
      rules+=`<text class="glab" x="${(rx+4).toFixed(1)}" y="${(y-3).toFixed(1)}" fill="${r.c}">${r.lab}</text>`; });

    // A single-series panel needs no legend — its title names the series.
    const leg = p.solo ? ''
      : p.kind==='flow'
      ? `<span class="lg"><i class="sw box" style="background:var(--pv)"></i>solar</span>
         <span class="lg"><i class="sw" style="background:var(--s1)"></i>battery power</span>`
      : p.series.map(q=>`<span class="lg"><i class="sw${p.kind==='stack'?' box':''}" style="background:${q.c}"></i>${q.lab}</span>`).join('');

    el.innerHTML = `<div class="phead"><div><span class="ptitle">${p.title}</span>
        <span class="psub"> ${p.sub}</span></div><div class="legend">${leg}</div></div>
      <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" style="height:${H}px">
        ${g}${xax}${marks}${rules}
        <g class="cross" style="display:none">
          <line y1="${PAD.t}" y2="${PAD.t+ih}" stroke="var(--ink-3)" stroke-width="1"/>
        </g>
      </svg>`;
    host.appendChild(el);
  });
  document.querySelector('#plots').style.setProperty('--iw','1');
}

/* ---- hover ------------------------------------------------------------------------- */
function slotAt(ev){
  const host=document.getElementById('plots');
  const sv=host.querySelector('svg'); const r=sv.getBoundingClientRect();
  const [a,b]=range(), n=b-a;
  const fx=(ev.clientX-r.left)/r.width*1000;
  const t=(fx-PAD.l)/(1000-PAD.l-PAD.r);
  if(t<-0.02||t>1.02) return null;
  return Math.max(a, Math.min(b-1, a+Math.round(t*(n-1))));
}
function fmtT(i){
  const d=Math.floor(i/SLOTS_PER_DAY), q=i%SLOTS_PER_DAY;
  return `Dec ${d+1} · ${String(Math.floor(q/4)).padStart(2,'0')}:${String((q%4)*15).padStart(2,'0')}`;
}
function hover(ev){
  const i=slotAt(ev), tip=document.getElementById('tip');
  const host=document.getElementById('plots');
  if(i===null){ tip.style.opacity=0; host.querySelectorAll('.cross').forEach(c=>c.style.display='none'); return; }
  const [a,b]=range(), n=b-a;
  const x=PAD.l+(i-a)*(1000-PAD.l-PAD.r)/(n-1||1);
  host.querySelectorAll('.panel').forEach(el=>{
    const c=el.querySelector('.cross'); c.style.display='';
    c.querySelector('line').setAttribute('x1',x); c.querySelector('line').setAttribute('x2',x);
  });
  const tierTxt=['not shaving','easing down (soft)','cutting (hard)'][S.tier[i]];
  const rows=[
    ['Grid — off', f2(kw(S.gridOff[i]))+' kW','var(--s2)'],
    ['Grid — as shipped', f2(kw(S.gridShip[i]))+' kW','var(--s1)'],
    ['Grid — ceiling-fill', f2(kw(S.gridFlat[i]))+' kW','var(--s3)'],
    ['Household base', f2(kw(S.base[i]))+' kW','var(--l1)'],
    ['Heat pump', f2(kw(S.hp[i]))+' kW','var(--l2)'],
    ['Wallbox', f2(kw(S.car[i]))+' kW','var(--l3)'],
    ['Sauna', f2(kw(S.sauna[i]))+' kW','var(--l4)'],
    ['Solar', f2(kw(S.pv[i]))+' kW','var(--pv)'],
    ['Battery', f2(kw(S.batt[i]))+' kW','var(--s1)'],
    ['Charge', (S.socShip[i]/10).toFixed(1)+' %',''],
    ['Price', (S.price[i]/1000).toFixed(3)+' €/kWh',''],
  ];
  tip.innerHTML=`<div class="th">${fmtT(i)} · ${tierTxt}</div><table>`+
    rows.map(r=>`<tr><td>${r[2]?`<i class="sw box" style="display:inline-block;background:${r[2]};margin-right:6px"></i>`:''}${r[0]}</td><td class="n">${r[1]}</td></tr>`).join('')+
    `</table><div class="why">${D.reasons[i]}<br><span style="color:var(--ink-3)">${D.peakReasons[i]}</span></div>`;
  const hr=host.getBoundingClientRect();
  const tw=248, th=tip.offsetHeight||300;
  let px=ev.clientX-hr.left+18;
  if(px+tw>hr.width) px=ev.clientX-hr.left-tw;
  tip.style.left=Math.max(6,Math.min(hr.width-tw,px))+'px';
  tip.style.top=Math.max(6,Math.min(hr.height-th-6, ev.clientY-hr.top-th/2))+'px';
  tip.style.opacity=1;
}

/* ---- table ------------------------------------------------------------------------- */
function table(){
  const h=['Day','Mode','°C','Solar','House','Heat pump','Car','Import','Peak off',
           'Peak shipped','Peak hold','Peak ceiling-fill','Uncapped','SoC min','Cost'];
  let s='<thead><tr>'+h.map(x=>`<th>${x}</th>`).join('')+'</tr></thead><tbody>';
  D.days.forEach((d,i)=>{
    const over=v=>v>4000?` class="over"`:'';
    s+=`<tr class="${i===day?'sel':''}"><td>${d.label}</td><td>${d.mode}</td>`+
       `<td>${d.outside_c.toFixed(0)}</td><td>${d.pv_kwh.toFixed(1)}</td>`+
       `<td>${d.house_kwh.toFixed(1)}</td><td>${d.hp_kwh.toFixed(1)}</td>`+
       `<td>${d.car_kwh.toFixed(1)}</td><td>${d.import_kwh.toFixed(1)}</td>`+
       `<td${over(d.peak_off_w)}>${f2(kw(d.peak_off_w))}</td>`+
       `<td${over(d.peak_w)}>${f2(kw(d.peak_w))}</td>`+
       `<td${over(d.peak_hold_w)}>${f2(kw(d.peak_hold_w))}</td>`+
       `<td${over(d.peak_flat_w)}>${f2(kw(d.peak_flat_w))}</td>`+
       `<td>${f2(kw(d.peak_uncapped_w))}</td><td>${d.soc_min.toFixed(0)}</td>`+
       `<td>${d.cost_eur.toFixed(2)}</td></tr>`;
  });
  document.getElementById('tbl').innerHTML=s+'</tbody>';
}

/* ---- wiring ------------------------------------------------------------------------ */
document.getElementById('dayBtns').innerHTML =
  D.days.map((d,i)=>`<button data-day="${i}">${d.label.replace('Dec ','')}</button>`).join('');
document.querySelector('.bar').addEventListener('click',e=>{
  const btn=e.target.closest('button[data-day]'); if(!btn) return;
  day=+btn.dataset.day;
  document.querySelectorAll('.bar button').forEach(b=>
    b.setAttribute('aria-pressed', String(+b.dataset.day===day)));
  build(); table();
});
const plots=document.getElementById('plots');
plots.addEventListener('mousemove',hover);
plots.addEventListener('mouseleave',()=>{
  document.getElementById('tip').style.opacity=0;
  plots.querySelectorAll('.cross').forEach(c=>c.style.display='none');
});

tiles(); build(); table();
</script>
"""


if __name__ == "__main__":
    print(f"wrote {build()}")
