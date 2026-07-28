#!/usr/bin/env python3
"""Compose dashboard-v2/index.html — V1 design system + V2 data model."""
import json, re
from pathlib import Path

BASE = Path(__file__).resolve().parent; PROJ = BASE.parent
v1 = (PROJ/"dashboard-v1"/"index.html").read_text(encoding="utf-8")
CSS = re.search(r'<style>(.*?)</style>', v1, re.S).group(1)   # reuse V1 design tokens verbatim
P   = json.loads((BASE/"payload_v2.json").read_text(encoding="utf-8"))

COLS = [
 ("Supplier","sup","t"),("Container","cont","t"),("Received Date","recv","d"),
 ("Component SKU","csku","t"),("Component Image","cimg","img"),("Component Created","ccre","d"),
 ("Combo SKU","bsku","t"),("Combo Image","bimg","img"),("Combo Created","bcre","d"),
 ("Marketplace","plat","t"),("Listing Status","stat","chip"),("Listed Date","ldate","d"),
 ("Impressions","impr","n"),("Clicks","clk","n"),("Orders","ord","n"),
 ("Sales (Units Sold)","units","n"),("Revenue","rev","money"),("Total Returns","ret","n"),
 ("Return Rate %","rrate","pct"),("Top Reason","reason","t"),
 ("Average Feedback","fb","fb"),
]

HTML = f"""<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Supplier's Basket to Customer's Home — Tracking System V2</title>
<style>{CSS}
/* ---- V2-only additions ---- */
td.imgcell{{padding:6px 13px}}
.v2img{{width:42px;height:42px;object-fit:cover;border-radius:7px;border:1px solid var(--line);background:var(--bg2);display:block}}
.v2noimg{{width:42px;height:42px;border-radius:7px;border:1px dashed var(--line);background:var(--bg2);display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:15px}}
.trunc{{max-width:210px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:inline-block;vertical-align:middle}}
.proxy{{border-bottom:1px dotted var(--orange);cursor:help}}
.btn.pg:disabled{{opacity:.4;cursor:default;border-color:var(--line);color:var(--muted)}}
.btn.pg:disabled:hover{{border-color:var(--line);color:var(--muted)}}
/* sidebar removed — main fills the full width, brand mark moves into the app bar */
.appbrand{{display:flex;align-items:center;flex:0 0 auto;margin-right:2px}}
.appbrand .brand-logo{{width:34px;height:34px;border-radius:9px;font-size:17px}}

/* ---- grouped table: one product block, many marketplace rows ---- */
/* Product cells span their group; marketplace cells sit to the right of a divider. */
td.pcol{{vertical-align:top;background:var(--bg2)}}
tbody tr.galt td.pcol{{background:var(--bg)}}
th.pcol{{background:var(--bg2)}}
/* divider between the Product section and the Marketplace section */
th.mstart,td.mstart{{border-left:2px solid var(--line)}}
/* a new product starts a visibly heavier rule */
tbody tr.gfirst > td{{border-top:2px solid var(--line)}}
tbody tr.gfirst:first-child > td{{border-top:0}}
/* keep marketplace rows of the same product visually tied together */
tbody tr.grp td.mcol{{border-bottom:1px solid var(--line2)}}
tbody tr.grp:hover td.mcol{{background:rgba(47,111,237,.05)}}
tbody tr.grp.galt td.mcol{{background:rgba(0,0,0,.012)}}
[data-theme="dark"] tbody tr.grp.galt td.mcol{{background:rgba(255,255,255,.02)}}
tbody tr.grp.galt:hover td.mcol{{background:rgba(47,111,237,.07)}}
/* product-level gap highlight (component with no combo) */
tbody tr.nocombo td.pcol{{background:rgba(224,49,49,.06)}}
tbody tr.galt.nocombo td.pcol{{background:rgba(224,49,49,.04)}}
td.mcol:first-of-type{{padding-left:16px}}   /* nested/indented feel */

/* view tabs live in the table panel header — reclaims the full-width block they
   used to occupy. phead wraps on narrow screens so nothing gets squeezed. */
.phead{{flex-wrap:wrap}}
.phead > div:first-child{{flex:1 1 260px}}
.phead #viewtabs{{flex:0 0 auto;margin-left:auto}}
@media(max-width:700px){{
  .phead #viewtabs{{margin-left:0;width:100%}}
  .phead #viewtabs .tab{{flex:1 1 0;text-align:center}}
}}
</style>
</head>
<body>
<div class="layout" id="layout">
  <div class="main">
    <header class="appbar">
      <div class="appbrand"><div class="brand-logo">📦</div></div>
      <div>
        <h1>Supplier's Basket → Customer's Home</h1>
        <div class="appsub">Tracking System · Version 2 · 2026 onwards</div>
      </div>
      <div class="spacer"></div>
      <div class="hmeta">
        <div class="hpill"><span class="hpill-ic">🧩</span><div><small>Components</small><b>{P['meta']['components']}</b></div></div>
        <div class="hpill"><span class="hpill-ic">🎁</span><div><small>Combos</small><b>{P['meta']['combos']}</b></div></div>
        <div class="hpill"><span class="hpill-ic">🕒</span><div><small>Captured</small><b>{P['capturedAt']}</b></div></div>
      </div>
      <button class="btn ghost" id="themeBtn">🌙 Theme</button>
      <button class="btn" id="csvBtn">⬇ CSV</button>
    </header>

    <div class="filterbar">
      <div class="fld"><label>Supplier</label><select id="f-sup"></select></div>
      <div class="fld"><label>Container</label><select id="f-cont"></select></div>
      <div class="fld"><label>Marketplace</label><select id="f-plat"></select></div>
      <div class="fld"><label>Listing Status</label><select id="f-stat">
        <option value="">All</option><option>Listed</option><option>Not Listed</option></select></div>
      <div class="fld"><label>Received from</label><div class="inp"><input type="date" id="f-rfrom"></div></div>
      <div class="fld"><label>Received to</label><div class="inp"><input type="date" id="f-rto"></div></div>
      <div class="fld"><label>Listed from</label><div class="inp"><input type="date" id="f-lfrom"></div></div>
      <div class="fld"><label>Listed to</label><div class="inp"><input type="date" id="f-lto"></div></div>
      <div class="fld grow"><label>Search</label><div class="inp"><span class="inp-ic">🔎</span>
        <input type="text" id="f-q" placeholder="SKU, supplier, container, PO, reason…"></div></div>
      <div class="fld"><span class="fld-spacer">&nbsp;</span><button class="tt-clear" id="clearBtn">Clear</button></div>
    </div>

    <div class="content">
      <div class="kpi-grid" id="kpi"></div>

      <div class="panel">
        <div class="phead">
          <div><h3>🗺️ Master Tracking Table <span class="muted">one Combo SKU × one marketplace per row</span></h3>
            <div class="sub">Component → Container → Combo → Listing → Traffic → Orders → Sales → Returns, in one view.
              <span class="muted" id="rowcount"></span></div></div>
          <div class="tablist" id="viewtabs">
            <button class="tab" data-view="comp">🧩 Components <b id="tabCompN"></b></button>
            <button class="tab active" data-view="combo">🎁 Combos <b id="tabComboN"></b></button>
          </div>
          <div class="perpage-wrap">Products
            <select class="perpage" id="perpage"><option value="50">50</option><option value="100" selected>100</option><option value="250">250</option><option value="1000">1000</option><option value="0">All</option></select>
          </div>
        </div>
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

<script>
const PAYLOAD = {json.dumps(P, separators=(',',':'))};
const B = PAYLOAD.B;
// Two independent datasets, identical column layout. Combos is the default view.
const DATA = {{ combo: PAYLOAD.rows, comp: PAYLOAD.rowsComp }};
let VIEW = 'combo';
let ROWS = DATA[VIEW];
const COLS = {json.dumps(COLS)};
const PLABEL = {{amazon:'Amazon', ebay:'eBay', shopify:'Shopify', 'b&q':'B&Q', wayfair:'Wayfair', other:'Other'}};

const esc = s => String(s==null?'':s).replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}})[c]);
const num = v => Number(v||0).toLocaleString();
const money = v => '£'+Number(v||0).toLocaleString(undefined,{{minimumFractionDigits:2,maximumFractionDigits:2}});
const fmtDate = d => {{ if(!d) return ''; const p=String(d).split('-'); if(p.length!==3) return d;
  return p[2]+' '+['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][+p[1]-1]+' '+p[0]; }};

const S = {{sup:'',cont:'',plat:'',stat:'',rfrom:'',rto:'',lfrom:'',lto:'',q:'',page:1,per:100,sort:null,dir:1}};

function opts(sel, vals, label){{
  sel.innerHTML = '<option value="">All '+label+'</option>' +
    vals.map(v=>'<option value="'+esc(v)+'">'+esc(PLABEL[v]||v)+'</option>').join('');
}}
const uniq = k => [...new Set(ROWS.map(r=>r[B[k]]).filter(Boolean))].sort();
// Filter option lists follow the active dataset, preserving the current choice
// when that value still exists in the new view.
function buildFilterOpts(){{
  [['f-sup','sup','suppliers'],['f-cont','cont','containers'],['f-plat','plat','marketplaces']]
    .forEach(([id,k,label])=>{{
      const el=document.getElementById(id), keep=S[k];
      opts(el, uniq(k), label);
      if(keep && [...el.options].some(o=>o.value===keep)) el.value=keep; else {{ el.value=''; S[k]=''; }}
    }});
}}

function filtered(){{
  return ROWS.filter(r=>{{
    if(S.sup  && r[B.sup]  !== S.sup)  return false;
    if(S.cont && r[B.cont] !== S.cont) return false;
    if(S.plat && r[B.plat] !== S.plat) return false;
    if(S.stat && r[B.stat] !== S.stat) return false;
    if(S.rfrom && (!r[B.recv]  || r[B.recv]  < S.rfrom)) return false;
    if(S.rto   && (!r[B.recv]  || r[B.recv]  > S.rto))   return false;
    if(S.lfrom && (!r[B.ldate] || r[B.ldate] < S.lfrom)) return false;
    if(S.lto   && (!r[B.ldate] || r[B.ldate] > S.lto))   return false;
    if(S.q){{
      const q=S.q.toLowerCase();
      const hay=[r[B.csku],r[B.bsku],r[B.sup],r[B.cont],r[B.po],r[B.reason],r[B.notes],r[B.dest]]
        .map(x=>String(x||'').toLowerCase()).join(' ');
      if(!hay.includes(q)) return false;
    }}
    return true;
  }});
}}

function kpis(rs){{
  const comps = new Set(rs.map(r=>r[B.csku]).filter(Boolean));
  const combos= new Set(rs.map(r=>r[B.bsku]).filter(Boolean));
  const noCombo = new Set(rs.filter(r=>!r[B.bsku]).map(r=>r[B.csku]));
  const listed = rs.filter(r=>r[B.stat]==='Listed').length;
  const sum = k => rs.reduce((a,r)=>a+(r[B[k]]||0),0);
  const units = sum('units'), rets = sum('ret');
  const card = (ic,label,val,sub,cls='') =>
    `<div class="kpi ${{cls}}"><div class="kpi-top"><div class="kpi-ic">${{ic}}</div>
      <div class="kpi-label">${{label}}<span class="kpi-note">${{sub||''}}</span></div></div>
      <div class="val">${{val}}</div></div>`;
  // The old "New Components" / "Combos Created" cards are now the view tabs above.
  const lead = VIEW==='combo'
    ? card('🚨','No Combo Yet', num(noCombo.size), 'components unused', 'gapkpi')
    : card('🚨','No Single Listing', num(new Set(rs.filter(r=>r[B.stat]!=='Listed').map(r=>r[B.csku])).size),
           'components unlisted', 'gapkpi');
  document.getElementById('kpi').innerHTML =
    lead +
    card('🛒','Listed Rows', num(listed), num(rs.length-listed)+' not listed') +
    card('👁','Impressions', num(sum('impr')), num(sum('clk'))+' clicks') +
    card('📦','Orders', num(sum('ord')), num(units)+' units sold') +
    card('💰','Revenue', money(sum('rev')), 'completed orders') +
    card('↩️','Return Rate', (units? (rets/units*100).toFixed(2):'0.00')+'%', num(rets)+' returned');
}}

function cell(r, key, type){{
  const v = r[B[key]];
  if(type==='img') return v ? `<img class="v2img" src="${{esc(v)}}" loading="lazy" referrerpolicy="no-referrer" alt="" onerror="this.outerHTML='&lt;div class=\\'v2noimg\\'&gt;🖼&lt;/div&gt;'">`
                            : `<div class="v2noimg">—</div>`;
  if(type==='d')    return v ? esc(fmtDate(v)) : '<span class="cell-mut">—</span>';
  if(type==='n')    return num(v);
  if(type==='money')return money(v);
  if(type==='pct')  return (Number(v||0)).toFixed(2)+'%';
  if(type==='chip') return v==='Listed' ? '<span class="chip green">Listed</span>'
                                        : '<span class="chip gray">Not Listed</span>';
  if(type==='fb'){{                       // [avg, count] -> "4.6★ (128 Reviews)"
    if(!v || !v.length) return '<span class="cell-mut">No Reviews</span>';
    const [avg,cnt] = v;
    return `<b>${{Number(avg).toFixed(1)}}★</b>` +
           (cnt ? ` <span class="cell-mut">(${{num(cnt)}} Review${{cnt==1?'':'s'}})</span>` : '');
  }}
  if(key==='plat')  return v ? esc(PLABEL[v]||v) : '<span class="cell-mut">—</span>';
  if(!v) return '<span class="cell-mut">—</span>';
  if(key==='reason'||key==='sup'||key==='bsku'||key==='csku')
    return `<span class="trunc" title="${{esc(v)}}">${{esc(v)}}</span>`;
  return esc(v);
}}

// ---------- grouping: one PRODUCT, many MARKETPLACE rows ----------
// COLS[0..8]  = product columns  (rendered once, via rowspan)
// COLS[9..20] = marketplace columns (one row each)
const PCOLS = COLS.slice(0,9), MCOLS = COLS.slice(9);
// Combos tab groups by Combo SKU, Components tab by Component SKU. In the combo
// view the metrics are keyed on the combo, so several component rows of the same
// combo carry identical numbers -- grouping removes that real duplication.
const groupKey = r => (VIEW==='combo' ? (r[B.bsku] || r[B.csku]) : r[B.csku]) || '—';

function groupRows(rs){{
  const m = new Map();
  for(const r of rs){{
    const k = groupKey(r);
    if(!m.has(k)) m.set(k, []);
    m.get(k).push(r);
  }}
  return [...m.values()].map(rows=>{{
    // B.comps carries every component behind this product (set by the builder,
    // which now emits ONE row per product x marketplace -- no duplicates).
    const cskus = [...new Set(rows.flatMap(r=>r[B.comps]||[r[B.csku]]).filter(Boolean))];
    return {{rows, head: rows[0], cskus}};
  }});
}}

function sortGroups(gs){{
  if(!S.sort) return gs;
  const k = S.sort, t = COLS.find(c=>c[1]===k)[2];
  const isProd = PCOLS.some(c=>c[1]===k);
  const val = g => {{
    if(isProd) return g.head[B[k]];
    if(['n','money','pct'].includes(t))      // rank products by their TOTAL
      return g.rows.reduce((a,r)=>a+(Number(r[B[k]])||0),0);
    if(t==='fb'){{                            // best rating in the group
      const v=g.rows.map(r=>r[B[k]]).filter(x=>x&&x.length).map(x=>Number(x[0]));
      return v.length?Math.max(...v):-1;
    }}
    return g.rows.map(r=>r[B[k]]).filter(Boolean).sort()[0] || '';
  }};
  const num_ = isProd ? ['n','money','pct'].includes(t) : true;
  return gs.sort((a,b)=>{{
    const x=val(a), y=val(b);
    if(typeof x==='number' && typeof y==='number') return (x-y)*S.dir;
    return String(x==null?'':x).localeCompare(String(y==null?'':y))*S.dir;
  }});
}}

function render(){{
  const rs = filtered();
  kpis(rs);
  const groups = sortGroups(groupRows(rs));

  document.getElementById('thead').innerHTML =
    COLS.map(([lbl,key,t],i)=>{{
      const cls=['n','money','pct'].includes(t)?'num sortable':'sortable';
      const seg = i<9 ? ' pcol' : '';
      const edge = i===9 ? ' mstart' : '';
      const on = S.sort===key;
      return `<th class="${{cls}}${{seg}}${{edge}}${{on?' sorted':''}}" data-k="${{key}}">${{esc(lbl)}}<span class="sarrow${{on?'':' dim'}}">${{on?(S.dir>0?'▲':'▼'):'⇅'}}</span></th>`;
    }}).join('');

  // Pagination now counts PRODUCTS, not marketplace rows.
  const per   = S.per > 0 ? S.per : Math.max(groups.length, 1);
  const pages = Math.max(1, Math.ceil(groups.length/per));
  if(S.page>pages) S.page=pages;
  const slice = groups.slice((S.page-1)*per, S.page*per);

  let html = '', gi = 0;
  for(const g of slice){{
    const n = g.rows.length, alt = (gi++ % 2) ? ' galt' : '';
    const gap = !g.head[B.bsku];
    g.rows.forEach((r, idx)=>{{
      const first = idx===0;
      html += `<tr class="grp${{alt}}${{first?' gfirst':''}}${{gap?' nocombo':''}}"`
            + (first?` title="${{esc(g.head[B.notes]||'')}}"`:'') + '>';
      if(first){{                                  // product block — rendered ONCE
        html += PCOLS.map(([lbl,key,t])=>{{
          const cls = (t==='img'?'imgcell ':'') + 'pcol';
          let inner;
          if(key==='csku' && g.cskus.length>1)     // multi-component combo
            inner = `<span class="trunc" title="${{esc(g.cskus.join(', '))}}">${{esc(g.cskus[0])}}</span>`
                  + ` <span class="cell-mut">+${{g.cskus.length-1}}</span>`;
          else inner = cell(g.head,key,t);
          return `<td class="${{cls}}" rowspan="${{n}}">${{inner}}</td>`;
        }}).join('');
      }}
      html += MCOLS.map(([lbl,key,t],j)=>{{
        const cls = (['n','money','pct'].includes(t)?'num ':'') + 'mcol' + (j===0?' mstart':'');
        return `<td class="${{cls}}">${{cell(r,key,t)}}</td>`;
      }}).join('');
      html += '</tr>';
    }});
  }}
  document.getElementById('tbody').innerHTML = html ||
    '<tr><td colspan="21" style="text-align:center;padding:40px;color:var(--muted)">No rows match these filters.</td></tr>';

  const totalGroups = groupRows(ROWS).length;
  document.getElementById('rowcount').textContent =
    `— ${{groups.length}} of ${{totalGroups}} products · ${{rs.length}} marketplace rows`;
  document.getElementById('pginfo').textContent =
    groups.length ? `Showing products ${{(S.page-1)*per+1}}–${{Math.min(S.page*per,groups.length)}} of ${{groups.length}}` : 'No products';
  document.getElementById('pgnum').textContent = ` ${{S.page}} / ${{pages}} `;
  document.getElementById('prev').disabled = S.page<=1;
  document.getElementById('next').disabled = S.page>=pages;
}}

document.getElementById('thead').addEventListener('click', e=>{{
  const th=e.target.closest('th[data-k]'); if(!th) return;
  const k=th.dataset.k; S.dir = (S.sort===k)? -S.dir : 1; S.sort=k; render();
}});
const bind=(id,key,ev='change')=>document.getElementById(id).addEventListener(ev,e=>{{S[key]=e.target.value;S.page=1;render();}});
bind('f-sup','sup'); bind('f-cont','cont'); bind('f-plat','plat'); bind('f-stat','stat');
bind('f-rfrom','rfrom'); bind('f-rto','rto'); bind('f-lfrom','lfrom'); bind('f-lto','lto');
bind('f-q','q','input');
document.getElementById('perpage').addEventListener('change',e=>{{S.per=+e.target.value;S.page=1;render();}});
document.getElementById('prev').addEventListener('click',()=>{{if(S.page>1){{S.page--;render();}}}});
document.getElementById('next').addEventListener('click',()=>{{S.page++;render();}});
document.getElementById('clearBtn').addEventListener('click',()=>{{
  Object.assign(S,{{sup:'',cont:'',plat:'',stat:'',rfrom:'',rto:'',lfrom:'',lto:'',q:'',page:1}});
  document.querySelectorAll('.filterbar select,.filterbar input').forEach(el=>el.value='');
  render();
}});
document.getElementById('themeBtn').addEventListener('click',()=>{{
  const d=document.documentElement; d.dataset.theme = d.dataset.theme==='dark'?'light':'dark';
}});
document.getElementById('csvBtn').addEventListener('click',()=>{{
  const rs=filtered();
  const head=COLS.map(c=>c[0]).join(',');
  const body=rs.map(r=>COLS.map(([l,k,t])=>{{
    let v=r[B[k]];
    if(t==='fb') v = (v&&v.length) ? (Number(v[0]).toFixed(1)+'* ('+v[1]+' Reviews)') : 'No Reviews';
    const s=String(v==null?'':v);
    return /[",\\n]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s;
  }}).join(',')).join('\\n');
  const blob=new Blob([head+'\\n'+body],{{type:'text/csv'}});
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob);
  a.download='scwts_v2_'+PAYLOAD.capturedAt+'.csv'; a.click();
}});

// ---------- view tabs: Components / Combos (no page reload) ----------
function setView(v){{
  if(v===VIEW) return;
  VIEW = v; ROWS = DATA[v];
  document.querySelectorAll('#viewtabs .tab').forEach(t=>t.classList.toggle('active', t.dataset.view===v));
  S.page = 1;                                   // filters/search/sort/per-page all persist
  buildFilterOpts();
  render();
}}
document.getElementById('viewtabs').addEventListener('click', e=>{{
  const t = e.target.closest('.tab[data-view]'); if(t) setView(t.dataset.view);
}});
document.getElementById('tabCompN').textContent  = '('+PAYLOAD.rowsComp.length+')';
document.getElementById('tabComboN').textContent = '('+PAYLOAD.rows.length+')';

buildFilterOpts();
render();
</script>
</body>
</html>
"""
out = PROJ/"dashboard-v2"/"index.html"
out.write_text(HTML, encoding="utf-8")
print(f"wrote {out}  ({out.stat().st_size:,} bytes)")
