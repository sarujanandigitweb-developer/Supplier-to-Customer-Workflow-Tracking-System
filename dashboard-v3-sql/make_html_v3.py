#!/usr/bin/env python3
"""
make_html_v3.py — composes dashboard-v3/index.html.

Reuses Dashboard V2's VISUAL design only (the <style> block), exactly as V2 reused
V1's. V3's data, columns and container logic are its own. V2 is never written to.

Differences from V2, per spec:
  - Supplier and Received Date columns REMOVED
  - Container tab list added; clicking a container filters to it
  - everything else (grouped product rows, filters, search, sort, paging,
    CSV export, theme, responsive behaviour) kept identical
"""
import json, re
from pathlib import Path

BASE = Path(__file__).resolve().parent
PROJ = BASE.parent
v2   = (PROJ / "dashboard-v2" / "index.html").read_text(encoding="utf-8")
CSS  = re.search(r'<style>(.*?)</style>', v2, re.S).group(1)     # design system only
P    = json.loads((BASE / "payload_v3.json").read_text(encoding="utf-8"))

# Supplier + Received Date deliberately absent.
COLS = [
 ("Component SKU","csku","t"),("Component Image","cimg","img"),("Component Created","ccre","d"),
 ("Combo SKU","bsku","t"),("Combo Image","bimg","img"),("Combo Created","bcre","d"),
 ("Marketplace","plat","t"),("Listing Status","stat","chip"),("Listed Date","ldate","d"),
 ("Impressions","impr","n"),("Clicks","clk","n"),("Orders","ord","n"),
 ("Sales (Units Sold)","units","n"),("Revenue","rev","money"),("Total Returns","ret","n"),
 ("Return Rate %","rrate","pct"),("Top Reason","reason","t"),("Average Feedback","fb","fb"),
]
NPROD = 6          # first 6 columns are the product block (rendered once per product)

HTML = f"""<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Container Tracking V3 — Supplier's Basket to Customer's Home</title>
<style>{CSS}
/* ---- V3-only ---- */
#conttabs{{flex-wrap:wrap; max-width:100%}}
#conttabs .tab b{{font-weight:800; margin-left:4px}}
</style>
</head>
<body>
<div class="layout" id="layout">
  <div class="main">
    <header class="appbar">
      <div class="appbrand"><div class="brand-logo">🚢</div></div>
      <div>
        <h1>Container Tracking — Supplier's Basket → Customer's Home</h1>
        <div class="appsub">Version 3 · Container → Component → Combo → Listing → Sales · 2026 UK containers</div>
      </div>
      <div class="spacer"></div>
      <div class="hmeta">
        <div class="hpill"><span class="hpill-ic">🚢</span><div><small>Containers</small><b>{P['meta']['containers']}</b></div></div>
        <div class="hpill"><span class="hpill-ic">🧩</span><div><small>Components</small><b>{P['meta']['components']}</b></div></div>
        <div class="hpill"><span class="hpill-ic">🎁</span><div><small>Combos</small><b>{P['meta']['combos']}</b></div></div>
        <div class="hpill"><span class="hpill-ic">🕒</span><div><small>Captured</small><b>{P['capturedAt']}</b></div></div>
      </div>
      <button class="btn ghost" id="themeBtn">🌙 Theme</button>
      <button class="btn" id="csvBtn">⬇ CSV</button>
    </header>

    <div class="filterbar">
      <div class="fld"><label for="f-plat">Marketplace</label><select id="f-plat"></select></div>
      <div class="fld"><label for="f-stat">Listing Status</label><select id="f-stat">
        <option value="">All</option><option>Listed</option><option>Not Listed</option></select></div>
      <div class="fld"><label for="f-lfrom">Listed from</label><div class="inp"><input type="date" id="f-lfrom"></div></div>
      <div class="fld"><label for="f-lto">Listed to</label><div class="inp"><input type="date" id="f-lto"></div></div>
      <div class="fld grow"><label for="f-q">Search</label><div class="inp"><span class="inp-ic">🔎</span>
        <input type="text" id="f-q" placeholder="Component SKU, Combo SKU, container…"></div></div>
      <div class="fld"><span class="fld-spacer">&nbsp;</span><button class="tt-clear" id="clearBtn">Clear</button></div>
    </div>

    <div class="content">
      <div class="kpi-grid" id="kpi"></div>

      <div class="panel">
        <div class="phead">
          <div><h3>🚢 Container Tracking Table <span class="muted">one product × one marketplace per row</span></h3>
            <div class="sub">Component SKUs come from the Google Sheet per container; everything else is fetched from PostgreSQL.
              <span class="muted" id="rowcount"></span></div></div>
          <div class="perpage-wrap"><label for="perpage">Products</label>
            <select class="perpage" id="perpage"><option value="50">50</option><option value="100" selected>100</option><option value="250">250</option><option value="1000">1000</option><option value="0">All</option></select>
          </div>
        </div>
        <div class="tablist" id="conttabs" style="margin-bottom:14px"></div>
        <div class="tablewrap">
          <table id="tbl"><thead><tr id="thead"></tr></thead><tbody id="tbody"></tbody></table>
        </div>
        <div class="pageinfo">
          <div class="pginfo-left"><span id="pginfo"></span></div>
          <div class="pagebtns">
            <button class="btn pg" id="prev">‹ Prev</button><span id="pgnum"></span><button class="btn pg" id="next">Next ›</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="drawer-bg hidden" id="drawerBg">
  <aside class="drawer" role="dialog" aria-modal="true" aria-labelledby="dTitle">
    <div class="dhead">
      <div>
        <div class="dtitle" id="dTitle"></div>
        <div class="dsub" id="dSub"></div>
      </div>
      <button type="button" class="dclose" id="dClose" aria-label="Close">&times;</button>
    </div>
    <div class="dbody onepage" id="dBody"></div>
  </aside>
</div>

<script>
const PAYLOAD = {json.dumps(P, separators=(',',':'))};
const B = PAYLOAD.B, ROWS = PAYLOAD.rows, CONTAINERS = PAYLOAD.containers;
const COLS = {json.dumps(COLS)};
const NPROD = {NPROD};
const PCOLS = COLS.slice(0,NPROD), MCOLS = COLS.slice(NPROD);
const PLABEL = {{amazon:'Amazon', ebay:'eBay', shopify:'Shopify', 'b&q':'B&Q', wayfair:'Wayfair', other:'Other'}};

const esc = s => String(s==null?'':s).replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}})[c]);
const num = v => Number(v||0).toLocaleString();
const money = v => '£'+Number(v||0).toLocaleString(undefined,{{minimumFractionDigits:2,maximumFractionDigits:2}});
const fmtDate = d => {{ if(!d) return ''; const p=String(d).split('-'); if(p.length!==3) return d;
  return p[2]+' '+['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][+p[1]-1]+' '+p[0]; }};

// CONTAINER is the primary selector; 'ALL' shows every container.
const RENDERED = [];   // render-order index -> {{r, g}} for the drawer
const S = {{cont:'ALL', plat:'', stat:'', lfrom:'', lto:'', q:'', page:1, per:100, sort:null, dir:1}};

function opts(sel, vals, label){{
  sel.innerHTML = '<option value="">All '+label+'</option>' +
    vals.map(v=>'<option value="'+esc(v)+'">'+esc(PLABEL[v]||v)+'</option>').join('');
}}
function inCont(r){{ return S.cont==='ALL' || r[B.cont]===S.cont; }}
function buildFilterOpts(){{
  const pool = ROWS.filter(inCont);
  const keep = S.plat;
  opts(document.getElementById('f-plat'),
       [...new Set(pool.map(r=>r[B.plat]).filter(Boolean))].sort(), 'marketplaces');
  const el = document.getElementById('f-plat');
  if(keep && [...el.options].some(o=>o.value===keep)) el.value=keep; else {{ el.value=''; S.plat=''; }}
}}

function buildTabs(){{
  const count = c => ROWS.filter(r=>c==='ALL'||r[B.cont]===c).length;
  document.getElementById('conttabs').innerHTML =
    ['ALL',...CONTAINERS].map(c=>
      `<button class="tab${{S.cont===c?' active':''}}" data-cont="${{esc(c)}}">`
      + `${{c==='ALL'?'🗂 All Containers':'🚢 '+esc(c)}} <b>(${{count(c)}})</b></button>`).join('');
}}

function filtered(){{
  return ROWS.filter(r=>{{
    if(!inCont(r)) return false;
    if(S.plat && r[B.plat] !== S.plat) return false;
    if(S.stat && r[B.stat] !== S.stat) return false;
    if(S.lfrom && (!r[B.ldate] || r[B.ldate] < S.lfrom)) return false;
    if(S.lto   && (!r[B.ldate] || r[B.ldate] > S.lto))   return false;
    if(S.q){{
      const q=S.q.toLowerCase();
      const comps=(r[B.comps]||[]).map(c=>c[0]).join(' ');
      const hay=[r[B.csku],r[B.bsku],r[B.cont],r[B.notes],comps]
        .map(x=>String(x||'').toLowerCase()).join(' ');
      if(!hay.includes(q)) return false;
    }}
    return true;
  }});
}}

function kpis(rs){{
  const comps = new Set(rs.flatMap(r=>(r[B.comps]||[]).map(c=>c[0])));
  const combos= new Set(rs.map(r=>r[B.bsku]).filter(Boolean));
  const listed= rs.filter(r=>r[B.stat]==='Listed').length;
  const sum = k => rs.reduce((a,r)=>a+(r[B[k]]||0),0);
  const units = sum('units'), rets = sum('ret');
  const card = (ic,label,val,sub,cls='') =>
    `<div class="kpi ${{cls}}"><div class="kpi-top"><div class="kpi-ic">${{ic}}</div>
      <div class="kpi-label">${{label}}<span class="kpi-note">${{sub||''}}</span></div></div>
      <div class="val">${{val}}</div></div>`;
  document.getElementById('kpi').innerHTML =
    card('🧩','Components', num(comps.size), S.cont==='ALL'?'all containers':S.cont) +
    card('🎁','Combos', num(combos.size), 'built from them') +
    card('🛒','Listed Rows', num(listed), num(rs.length-listed)+' not listed') +
    card('👁','Impressions', num(sum('impr')), num(sum('clk'))+' clicks') +
    card('📦','Orders', num(sum('ord')), num(units)+' units sold') +
    card('💰','Revenue', money(sum('rev')), 'completed orders');
}}

function cell(r, key, type){{
  const v = r[B[key]];
  if(type==='img') return v ? `<img class="v2img" src="${{esc(v)}}" loading="lazy" referrerpolicy="no-referrer" alt="" onerror="this.outerHTML='&lt;div class=\\\\'v2noimg\\\\'&gt;🖼&lt;/div&gt;'">`
                            : `<div class="v2noimg">—</div>`;
  if(type==='d')    return v ? esc(fmtDate(v)) : '<span class="cell-mut">—</span>';
  if(type==='n')    return num(v);
  if(type==='money')return money(v);
  if(type==='pct')  return (Number(v||0)).toFixed(2)+'%';
  if(type==='chip') return v==='Listed' ? '<span class="chip green">Listed</span>'
                                        : '<span class="chip gray">Not Listed</span>';
  if(type==='fb'){{
    if(!v || !v.length) return '<span class="cell-mut">No Reviews</span>';
    return `<b>${{Number(v[0]).toFixed(1)}}★</b>`+(v[1]?` <span class="cell-mut">(${{num(v[1])}} Reviews)</span>`:'');
  }}
  if(key==='plat')  return v ? esc(PLABEL[v]||v) : '<span class="cell-mut">—</span>';
  if(!v) return '<span class="cell-mut">—</span>';
  return `<span class="trunc" title="${{esc(v)}}">${{esc(v)}}</span>`;
}}

// product identity = the combo when present, else the component
const groupKey = r => (r[B.cont]||'') + '||' + ((r[B.bsku] || r[B.csku]) || '—');
function groupRows(rs){{
  const m = new Map();
  for(const r of rs){{ const k=groupKey(r); if(!m.has(k)) m.set(k,[]); m.get(k).push(r); }}
  return [...m.values()].map(rows=>{{
    const seen=new Set(), comps=[];
    for(const c of rows.flatMap(r=>r[B.comps]||[]))
      if(c && c[0] && !seen.has(c[0])) {{ seen.add(c[0]); comps.push(c); }}
    return {{rows, head: rows[0], comps}};
  }});
}}
function sortGroups(gs){{
  if(!S.sort) return gs;
  const k=S.sort, t=COLS.find(c=>c[1]===k)[2], isProd = PCOLS.some(c=>c[1]===k);
  const val = g => {{
    if(isProd) return g.head[B[k]];
    if(['n','money','pct'].includes(t)) return g.rows.reduce((a,r)=>a+(Number(r[B[k]])||0),0);
    if(t==='fb'){{ const v=g.rows.map(r=>r[B[k]]).filter(x=>x&&x.length).map(x=>Number(x[0]));
                  return v.length?Math.max(...v):-1; }}
    return g.rows.map(r=>r[B[k]]).filter(Boolean).sort()[0] || '';
  }};
  return gs.sort((a,b)=>{{ const x=val(a), y=val(b);
    if(typeof x==='number' && typeof y==='number') return (x-y)*S.dir;
    return String(x==null?'':x).localeCompare(String(y==null?'':y))*S.dir; }});
}}

// component-level columns list EVERY component; combo columns render once
const CI = {{csku:0, cimg:1, ccre:2}};
function prodCell(g, key, t){{
  const comps = (g.comps && g.comps.length) ? g.comps : null;
  if(!comps) return cell(g.head, key, t);
  if(key==='cimg'){{
    return '<div class="cimgs">' + comps.map(c=> c[CI.cimg]
      ? `<img class="v2img" src="${{esc(c[CI.cimg])}}" loading="lazy" referrerpolicy="no-referrer" alt="${{esc(c[CI.csku])}}" title="${{esc(c[CI.csku])}}" onerror="this.outerHTML='&lt;div class=\\\\'v2noimg\\\\'&gt;🖼&lt;/div&gt;'">`
      : `<div class="v2noimg" title="${{esc(c[CI.csku])}}">—</div>`).join('') + '</div>';
  }}
  if(key==='csku')
    return '<div class="clist">' + comps.map(c=>
      `<span class="citem" title="${{esc(c[CI.csku])}}">${{esc(c[CI.csku])}}</span>`).join('') + '</div>';
  if(key==='ccre')
    return '<div class="clist">' + comps.map(c=>
      `<span class="citem">${{c[CI.ccre]?esc(fmtDate(c[CI.ccre])):'<span class="cell-mut">—</span>'}}</span>`).join('') + '</div>';
  return cell(g.head, key, t);
}}

function render(){{
  const rs = filtered();
  kpis(rs);
  const groups = sortGroups(groupRows(rs));

  document.getElementById('thead').innerHTML = COLS.map(([lbl,key,t],i)=>{{
    const cls=['n','money','pct'].includes(t)?'num sortable':'sortable';
    const seg = i<NPROD ? ' pcol' : '';
    const edge = i===NPROD ? ' mstart' : '';
    const on = S.sort===key;
    return `<th class="${{cls}}${{seg}}${{edge}}${{on?' sorted':''}}" data-k="${{key}}">${{esc(lbl)}}<span class="sarrow${{on?'':' dim'}}">${{on?(S.dir>0?'▲':'▼'):'⇅'}}</span></th>`;
  }}).join('');

  const per   = S.per > 0 ? S.per : Math.max(groups.length,1);
  const pages = Math.max(1, Math.ceil(groups.length/per));
  if(S.page>pages) S.page=pages;
  const slice = groups.slice((S.page-1)*per, S.page*per);

  let html='', gi=0;
  RENDERED.length = 0;
  for(const g of slice){{
    const n=g.rows.length, alt=(gi++%2)?' galt':'';
    const gap = !g.head[B.bsku];
    g.rows.forEach((r,idx)=>{{
      const first = idx===0;
      const ix = RENDERED.push({{r, g}}) - 1;
      html += `<tr class="grp${{alt}}${{first?' gfirst':''}}${{gap?' nocombo':''}}" data-ix="${{ix}}"`
            + (first?` title="${{esc(g.head[B.notes]||'')}}"`:'') + '>';
      if(first) html += PCOLS.map(([lbl,key,t])=>
        `<td class="${{(t==='img'?'imgcell ':'')}}pcol" rowspan="${{n}}">${{prodCell(g,key,t)}}</td>`).join('');
      html += MCOLS.map(([lbl,key,t],j)=>
        `<td class="${{(['n','money','pct'].includes(t)?'num ':'')}}mcol${{j===0?' mstart':''}}">${{cell(r,key,t)}}</td>`).join('');
      html += '</tr>';
    }});
  }}
  document.getElementById('tbody').innerHTML = html ||
    `<tr><td colspan="${{COLS.length}}" style="text-align:center;padding:40px;color:var(--muted)">No rows match these filters.</td></tr>`;

  const totalGroups = groupRows(ROWS.filter(inCont)).length;
  document.getElementById('rowcount').textContent =
    ` — ${{groups.length}} of ${{totalGroups}} products · ${{rs.length}} marketplace rows`;
  document.getElementById('pginfo').textContent =
    groups.length ? `Showing products ${{(S.page-1)*per+1}}–${{Math.min(S.page*per,groups.length)}} of ${{groups.length}}` : 'No products';
  document.getElementById('pgnum').textContent = ` ${{S.page}} / ${{pages}} `;
  document.getElementById('prev').disabled = S.page<=1;
  document.getElementById('next').disabled = S.page>=pages;
}}

// ---------- detail drawer: EVERY field for one record, on one page ----------
// Same UI as Dashboard V2. V3 has no Supplier/Received Date, so that card is
// replaced by the Container card (the Google-Sheet mapping that defines V3).
const fld = (label, val, cls='') =>
  `<div class="dfield ${{cls}}"><span class="dlabel">${{esc(label)}}</span><span class="dval ${{cls.includes('money')?'money':''}}">${{val}}</span></div>`;
const txt = v => (v===0 || v) && String(v).trim() !== '' ? esc(v) : '<span class="cell-mut">—</span>';
const dt  = v => v ? esc(fmtDate(v)) : '<span class="cell-mut">—</span>';
const pic = (url,label) => `<div class="dimg">${{url
  ? `<img src="${{esc(url)}}" loading="lazy" referrerpolicy="no-referrer" alt="" onerror="this.outerHTML='&lt;div class=\\'v2noimg\\'&gt;🖼&lt;/div&gt;'">`
  : '<div class="v2noimg">—</div>'}}<small>${{esc(label)}}</small></div>`;

function openDetail(ix){{
  const rec = RENDERED[ix]; if(!rec) return;
  const {{r, g}} = rec;
  const comps = (g.comps && g.comps.length) ? g.comps : [[r[B.csku], r[B.cimg], r[B.ccre]]];
  const isCombo = !!r[B.bsku];

  document.getElementById('dTitle').textContent = r[B.bsku] || r[B.csku] || '—';
  document.getElementById('dSub').innerHTML =
    `<span>🚢 ${{esc(r[B.cont]||'—')}}</span><span class="dsep">·</span>` +
    `<span>${{isCombo?'🎁 Combo':'🧩 Component'}}</span><span class="dsep">·</span>` +
    `<span>${{esc(PLABEL[r[B.plat]] || r[B.plat] || 'No marketplace')}}</span><span class="dsep">·</span>` +
    (r[B.stat]==='Listed' ? '<span class="chip green">Listed</span>' : '<span class="chip gray">Not Listed</span>');

  // comps entries are [sku, image, created]; collapse when all components agree
  const stack = (i, fmt=txt) => {{
    const v = comps.map(c=>c[i]);
    if(new Set(v.map(x=>String(x==null?'':x))).size === 1) return fmt(v[0]);
    return '<span class="dstack">' + v.map(x=>`<span>${{fmt(x)}}</span>`).join('') + '</span>';
  }};

  const rate = Number(r[B.rrate]||0);
  document.getElementById('dBody').innerHTML = `
    <div class="dcard span3">
      <div class="dctitle">🖼 Images &amp; identity</div>
      <div style="display:flex;gap:16px;align-items:flex-start;flex-wrap:wrap">
        <div class="dimgrow">
          ${{comps.map(c=>pic(c[1], 'Component')).join('')}}
          ${{isCombo ? pic(r[B.bimg], 'Combo') : ''}}
        </div>
        <div class="dgrid" style="flex:1 1 320px;grid-template-columns:1fr 1fr">
          ${{fld('Component SKU',     stack(0))}}
          ${{fld('Component Created', stack(2, dt))}}
          ${{isCombo ? fld('Combo SKU', txt(r[B.bsku])) : ''}}
          ${{isCombo ? fld('Combo Created', dt(r[B.bcre])) : ''}}
        </div>
      </div>
    </div>

    <div class="dcard span2">
      <div class="dctitle">🚢 Container</div>
      <div class="dgrid" style="grid-template-columns:1fr 1fr">
        ${{fld('Container',   txt(r[B.cont]))}}
        ${{fld('Components in this product', txt(comps.length))}}
        ${{fld('Source', 'Google Sheet — <i>New Containers to UK - 2026</i>', 'wide')}}
      </div>
    </div>

    <div class="dcard">
      <div class="dctitle">🛒 Listing</div>
      <div class="dgrid" style="grid-template-columns:1fr">
        ${{fld('Marketplace',    txt(PLABEL[r[B.plat]] || r[B.plat]))}}
        ${{fld('Listing Status', r[B.stat]==='Listed'?'<span class="chip green">Listed</span>':'<span class="chip gray">Not Listed</span>')}}
        ${{fld('Listed Date',    dt(r[B.ldate]))}}
        ${{fld('Listing URL', String(r[B.url]||'').startsWith('http')
            ? `<a class="plink" href="${{esc(r[B.url])}}" target="_blank" rel="noopener noreferrer">Open listing ↗</a>`
            : '<span class="cell-mut">—</span>')}}
      </div>
    </div>

    <div class="dcard span2">
      <div class="dctitle">📈 Performance <span class="cell-mut" style="font-weight:500;text-transform:none;letter-spacing:0">— Listed Date → today</span></div>
      <div class="dgrid" style="grid-template-columns:repeat(3,1fr)">
        ${{fld('Impressions', txt(num(r[B.impr]||0)))}}
        ${{fld('Clicks',      txt(num(r[B.clk]||0)))}}
        ${{fld('Orders',      txt(num(r[B.ord]||0)))}}
        ${{fld('Units Sold',  txt(num(r[B.units]||0)))}}
        ${{fld('Revenue',     money(r[B.rev]||0), 'money')}}
      </div>
    </div>

    <div class="dcard">
      <div class="dctitle">↩️ Returns &amp; feedback</div>
      <div class="dgrid" style="grid-template-columns:1fr 1fr">
        ${{fld('Total Returns', txt(num(r[B.ret]||0)))}}
        ${{fld('Return Rate %', `<span class="chip ${{rate>10?'red':rate>0?'orange':'gray'}}">${{rate.toFixed(2)}}%</span>`)}}
        ${{fld('Top Reason',      txt(r[B.reason]), 'wide')}}
        ${{fld('Average Feedback',cell(r,'fb','fb'), 'wide')}}
      </div>
    </div>

    ${{r[B.notes] ? `<div class="dcard span3"><div class="dctitle">📝 Notes</div>
        <div class="dval" style="font-weight:500;font-size:12.5px">${{esc(r[B.notes])}}</div></div>` : ''}}`;

  const bg = document.getElementById('drawerBg');
  bg.classList.remove('hidden');
  void bg.offsetWidth;          // force reflow so .open animates instead of
  bg.classList.add('open');     // leaving an invisible overlay swallowing clicks
  document.body.style.overflow = 'hidden';
}}
function closeDetail(){{
  const bg = document.getElementById('drawerBg');
  bg.classList.remove('open');
  document.body.style.overflow = '';
  setTimeout(()=>bg.classList.add('hidden'), 200);
}}
document.getElementById('tbody').addEventListener('click', e=>{{
  if(e.target.closest('a')) return;                 // let listing links work
  const tr = e.target.closest('tr[data-ix]');
  if(tr) openDetail(+tr.dataset.ix);
}});
document.getElementById('dClose').addEventListener('click', closeDetail);
document.getElementById('drawerBg').addEventListener('click', e=>{{
  if(e.target.id === 'drawerBg') closeDetail();
}});
document.addEventListener('keydown', e=>{{ if(e.key === 'Escape') closeDetail(); }});

// ---------- container tabs: filter to one container, no page reload ----------
document.getElementById('conttabs').addEventListener('click', e=>{{
  const t=e.target.closest('.tab[data-cont]'); if(!t) return;
  S.cont = t.dataset.cont; S.page = 1;
  buildTabs(); buildFilterOpts(); render();
}});
document.getElementById('thead').addEventListener('click', e=>{{
  const th=e.target.closest('th[data-k]'); if(!th) return;
  const k=th.dataset.k; S.dir=(S.sort===k)?-S.dir:1; S.sort=k; render();
}});
const bind=(id,key,ev='change')=>document.getElementById(id).addEventListener(ev,e=>{{S[key]=e.target.value;S.page=1;render();}});
bind('f-plat','plat'); bind('f-stat','stat'); bind('f-lfrom','lfrom'); bind('f-lto','lto'); bind('f-q','q','input');
document.getElementById('perpage').addEventListener('change',e=>{{S.per=+e.target.value;S.page=1;render();}});
document.getElementById('prev').addEventListener('click',()=>{{if(S.page>1){{S.page--;render();}}}});
document.getElementById('next').addEventListener('click',()=>{{S.page++;render();}});
document.getElementById('clearBtn').addEventListener('click',()=>{{
  Object.assign(S,{{plat:'',stat:'',lfrom:'',lto:'',q:'',page:1}});
  document.querySelectorAll('.filterbar select,.filterbar input').forEach(el=>el.value='');
  render();
}});
document.getElementById('themeBtn').addEventListener('click',()=>{{
  const d=document.documentElement; d.dataset.theme = d.dataset.theme==='dark'?'light':'dark';
}});
document.getElementById('csvBtn').addEventListener('click',()=>{{
  const rs=filtered();
  const head=['Container',...COLS.map(c=>c[0])].join(',');
  const body=rs.map(r=>['Container',...COLS.map(c=>c[1])].map((k,i)=>{{
    let v = i===0 ? r[B.cont] : r[B[k]];
    const t = i===0 ? 't' : COLS[i-1][2];
    if(t==='fb') v = (v&&v.length) ? (Number(v[0]).toFixed(1)+'* ('+v[1]+' Reviews)') : 'No Reviews';
    const s=String(v==null?'':v);
    return /[",\\n]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s;
  }}).join(',')).join('\\n');
  const blob=new Blob([head+'\\n'+body],{{type:'text/csv'}});
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob);
  a.download='scwts_v3_'+PAYLOAD.capturedAt+'.csv'; a.click();
}});

buildTabs(); buildFilterOpts(); render();
</script>
</body>
</html>
"""
out = PROJ / "dashboard-v3" / "index.html"
out.parent.mkdir(exist_ok=True)
out.write_text(HTML, encoding="utf-8")
print(f"wrote {out}  ({out.stat().st_size:,} bytes)")
