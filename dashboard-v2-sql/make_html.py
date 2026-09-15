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
/* product-level gap highlight (component with no combo) */
tbody tr.nocombo td.pcol{{background:rgba(224,49,49,.06)}}
tbody tr.galt.nocombo td.pcol{{background:rgba(224,49,49,.04)}}
td.mcol:first-of-type{{padding-left:16px}}   /* nested/indented feel */

/* the table shows only the essential columns; everything else lives in the
   click-through drawer, so the grid stays scannable instead of 21 columns wide */
tbody tr.grp{{cursor:pointer}}

/* ---- Record ID: pinned left, always visible while scrolling ----
   Sticky cells MUST be fully opaque or the columns sliding underneath show
   through and smear into the text. So the solid theme colour is the
   background-COLOR and any hover tint is layered on as a background-IMAGE.
   z-index ladder: body cells < pinned body cell(3) < header(4) < pinned header(6). */
th.ridcol,td.ridcol{{
  position:sticky; left:0;
  white-space:nowrap; font-variant-numeric:tabular-nums;
  font-weight:700; font-size:12px; letter-spacing:.01em;
  border-right:2px solid var(--line);
}}
/* The Record ID sits in the PRODUCT zone, so it must use the SAME banding as
   td.pcol -- var(--bg2)/var(--bg) -- not the card palette, or the pinned column
   reads as a mismatched white stripe against the product cells. The gap tints
   are the opaque equivalents of pcol's rgba() reds (a sticky cell cannot be
   translucent without the scrolling columns bleeding through). */
thead th.ridcol{{z-index:6; background-color:var(--bg2)}}
tbody td.ridcol{{z-index:3; background-color:var(--bg2); color:var(--muted); vertical-align:top}}
tbody tr.galt td.ridcol{{background-color:var(--bg)}}
tbody tr.nocombo td.ridcol{{background-color:#ede5eb}}
tbody tr.galt.nocombo td.ridcol{{background-color:#f3eef2}}
[data-theme="dark"] tbody td.ridcol{{background-color:var(--bg2)}}
[data-theme="dark"] tbody tr.galt td.ridcol{{background-color:var(--bg)}}
[data-theme="dark"] tbody tr.nocombo td.ridcol{{background-color:#1f1b25}}
[data-theme="dark"] tbody tr.galt.nocombo td.ridcol{{background-color:#17151d}}
/* hover: product cells are not tinted on hover, so the pinned cell isn't
   either -- only the text sharpens, keeping the two zones consistent */
tbody tr.grp:hover td.ridcol{{color:var(--text)}}

/* ---- the table scrolls on BOTH axes, header stays put ----
   .main/.content/.panel form a full-height flex column (from the V1 shell), so
   .tablewrap absorbs the leftover height and scrolls internally. Explicit here
   so the behaviour survives regardless of rule order. */
.panel .tablewrap{{
  /* set each axis explicitly -- the `overflow` shorthand was leaving
     overflow-y as `visible`, so only horizontal scrolling worked */
  overflow-x:auto; overflow-y:auto;
  flex:1 1 auto; min-height:220px; max-height:calc(100vh - 300px);
  overscroll-behavior:contain;   /* don't chain the scroll to the page at the edges */
}}
.panel table{{min-width:max-content}}   /* never squeeze columns -- scroll instead */
.panel thead th{{position:sticky; top:-1px; z-index:4}}
.panel thead th.ridcol{{z-index:6}}  /* header survives vertical scroll */
.tablehint{{font-size:12px;color:var(--muted);margin-top:10px}}
.dimgrow{{display:flex;gap:14px;flex-wrap:wrap}}
.dimg{{text-align:center}}
.dimg img,.dimg .v2noimg{{width:96px;height:96px;border-radius:12px;object-fit:cover;
  border:1px solid var(--line);background:var(--card);display:block}}
.dimg .v2noimg{{display:flex;align-items:center;justify-content:center;font-size:26px}}
.dimg small{{display:block;margin-top:6px;font-size:10px;font-weight:700;
  text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}}
.dfield{{display:flex;flex-direction:column;gap:3px;min-width:0}}
.dfield .dlabel{{font-size:9.5px;font-weight:700;text-transform:uppercase;
  letter-spacing:.05em;color:var(--muted)}}
.dfield .dval{{font-size:13.5px;font-weight:600;color:var(--text);word-break:break-word;line-height:1.35}}
.dfield .dval.money{{color:var(--accent);font-size:15px;font-weight:800}}
.dfield.wide{{grid-column:1 / -1}}
.dstack{{display:flex;flex-direction:column;gap:4px}}
/* safety: only the opened drawer may capture pointer events, so a stuck
   overlay can never block the dashboard underneath it */
.drawer-bg{{pointer-events:none}}
.drawer-bg.open{{pointer-events:auto}}

/* ---- ONE-PAGE drawer: every field visible at once, no scrolling ----
   Wider panel + a 3-column card grid that fills the available height. */
.drawer{{width:min(640px,100%)}}
.dbody.onepage{{
  overflow:hidden;                 /* never scroll -- everything must fit */
  padding:14px 16px; gap:12px;
  display:grid !important; align-content:start;
  grid-template-columns:repeat(2,1fr);
  grid-auto-rows:minmax(0,auto);
  height:100%;
}}
.dbody.onepage .dcard{{padding:11px 13px; min-height:0; overflow:hidden}}
.dbody.onepage .dctitle{{margin-bottom:8px; font-size:10.5px}}
.dbody.onepage .dgrid{{grid-template-columns:1fr 1fr; gap:9px 12px}}
.dcard.span2{{grid-column:1 / -1}}
.dcard.span3{{grid-column:1 / -1}}
.dfield .dval{{font-size:13px}}
.dfield .dval.money{{font-size:14.5px}}
.dimgrow{{gap:10px}}
.dimg img,.dimg .v2noimg{{width:74px;height:74px}}
/* shrink gracefully on shorter screens so it still fits without scrolling */
@media(max-height:820px){{
  .dbody.onepage{{gap:9px;padding:11px 13px}}
  .dbody.onepage .dcard{{padding:9px 11px}}
  .dbody.onepage .dctitle{{margin-bottom:6px}}
  .dfield .dval{{font-size:12.5px}}
  .dimg img,.dimg .v2noimg{{width:62px;height:62px}}
}}
@media(max-height:680px){{
  .dfield .dlabel{{font-size:9px}}
  .dfield .dval{{font-size:11.5px}}
  .dimg img,.dimg .v2noimg{{width:52px;height:52px}}
  .dbody.onepage .dgrid{{gap:7px 10px}}
}}
@media(max-width:620px){{
  .dbody.onepage{{grid-template-columns:1fr}}
  .dcard.span2,.dcard.span3{{grid-column:1 / -1}}
}}
@media(max-width:640px){{
  .dbody.onepage{{grid-template-columns:1fr; overflow:auto}}   /* phones: allow scroll */
  .dcard.span2,.dcard.span3{{grid-column:auto}}
}}

/* stacked component values inside ONE product cell — every component on its own
   line, aligned across Supplier / Container / Received / SKU / Image / Created */
.pstack{{display:flex;flex-direction:column}}
.pstack .pitem{{
  min-height:52px; display:flex; align-items:center;
  padding:3px 0; border-bottom:1px dashed var(--line);
}}
.pstack .pitem:last-child{{border-bottom:0}}
td.pcol{{white-space:normal}}

/* ---- per-marketplace row tint: each channel gets its own light background so
   Amazon / eBay / Shopify rows separate at a glance. Declared AFTER the zebra
   rules so it wins the cascade; hover is declared after this to still win. ---- */
tbody tr.mk-amazon  td.mcol{{background:#ffeed9}}
tbody tr.mk-ebay    td.mcol{{background:#e7effe}}
tbody tr.mk-shopify td.mcol{{background:#e3f6ec}}
tbody tr.mk-bq      td.mcol{{background:#f0eafc}}
tbody tr.mk-wayfair td.mcol{{background:#e3f3f6}}
tbody tr.mk-other   td.mcol{{background:#ebeef2}}
tbody tr.mk-none    td.mcol{{background:var(--card)}}
/* colour key on the leading marketplace cell */
tbody tr.mk-amazon  td.mstart{{box-shadow:inset 3px 0 0 rgba(240,140,0,.55)}}
tbody tr.mk-ebay    td.mstart{{box-shadow:inset 3px 0 0 rgba(47,111,237,.55)}}
tbody tr.mk-shopify td.mstart{{box-shadow:inset 3px 0 0 rgba(18,184,134,.55)}}
tbody tr.mk-bq      td.mstart{{box-shadow:inset 3px 0 0 rgba(112,72,232,.55)}}
tbody tr.mk-wayfair td.mstart{{box-shadow:inset 3px 0 0 rgba(12,133,153,.55)}}
tbody tr.mk-other   td.mstart{{box-shadow:inset 3px 0 0 var(--gray)}}

[data-theme="dark"] tbody tr.mk-amazon  td.mcol{{background:#2b2113}}
[data-theme="dark"] tbody tr.mk-ebay    td.mcol{{background:#131f33}}
[data-theme="dark"] tbody tr.mk-shopify td.mcol{{background:#122720}}
[data-theme="dark"] tbody tr.mk-bq      td.mcol{{background:#1e1830}}
[data-theme="dark"] tbody tr.mk-wayfair td.mcol{{background:#102529}}
[data-theme="dark"] tbody tr.mk-other   td.mcol{{background:#191f28}}
[data-theme="dark"] tbody tr.mk-none    td.mcol{{background:var(--card)}}

/* HOVER — must not flatten the marketplace colours. A background-color override
   would repaint every row the same blue and destroy the per-channel hue, so the
   tint stays as the background-COLOR and the hover darkening is layered on top
   as a background-IMAGE. Each channel keeps its own hue while hovering. */
/* Scoped to td.mcol ONLY. The product cells carry rowspan, so they live in the
   group's FIRST <tr> -- including td.pcol here made hovering that first row light
   up the whole product block, while hovering any later row lit only the
   marketplace cells. Marketplace-only keeps every row behaving identically. */
tbody tr.grp:hover td.mcol{{
  background-image:linear-gradient(rgba(20,30,50,.13),rgba(20,30,50,.13));
}}
[data-theme="dark"] tbody tr.grp:hover td.mcol{{
  background-image:linear-gradient(rgba(255,255,255,.09),rgba(255,255,255,.09));
}}
/* crisp rule on the hovered marketplace row only */
tbody tr.grp:hover td.mcol{{
  border-top:1px solid var(--accent); border-bottom:1px solid var(--accent);
}}

/* view tabs live in the table panel header — reclaims the full-width block they
   used to occupy. phead wraps on narrow screens so nothing gets squeezed. */
.phead{{flex-wrap:wrap}}
.phead > div:first-child{{flex:1 1 260px}}
.phead #viewtabs{{flex:0 0 auto;margin-left:auto}}
@media(max-width:700px){{
  .phead #viewtabs{{margin-left:0;width:100%}}
  .phead #viewtabs .tab{{flex:1 1 0;text-align:center}}
}}
/* ---- HEADER vs BODY separation -------------------------------------------
   thead th inherited background:var(--bg2) from V1 — the exact same token the
   product cells (td.pcol) and the Record ID column use, so the header read as
   just another data row. Give the header its own deeper tone plus a solid
   2px rule, and make its label type stronger. Declared last so it wins over
   the .pcol / .ridcol background rules above. */
thead th,
thead th.pcol,
thead th.ridcol,
.panel thead th{{
  background-color:#dbe2ed !important;
  color:#4a586d;
  font-weight:800;
  letter-spacing:.045em;
  border-bottom:2px solid #c3cddc;
  box-shadow:inset 0 -1px 0 #c3cddc;
}}
thead th.mstart{{border-left:2px solid #c3cddc}}
thead th.sorted{{color:var(--accent)}}
[data-theme="dark"] thead th,
[data-theme="dark"] thead th.pcol,
[data-theme="dark"] thead th.ridcol,
[data-theme="dark"] .panel thead th{{
  background-color:#202b3b !important;
  color:#a8b8cd;
  border-bottom:2px solid #38455a;
  box-shadow:inset 0 -1px 0 #38455a;
}}
[data-theme="dark"] thead th.mstart{{border-left:2px solid #38455a}}
[data-theme="dark"] thead th.sorted{{color:var(--accent)}}
/* ---- compact table footer ----------------------------------------------
   The footer was three stacked bands: a full-width hint line, the pager row,
   and the panel's 18px bottom padding. The hint now shares the pager row and
   the remaining paddings are tightened, cutting ~40px of dead height without
   losing any control or information. */
.tablehint{{margin-top:0; font-size:11.5px; opacity:.85}}
.panel .pageinfo{{
  margin-top:0; padding-top:6px; gap:10px;
  border-top:1px solid var(--line2);   /* separates footer from the table body */
  font-size:12px; min-height:0;
}}
.panel .pginfo-left{{gap:12px; row-gap:2px}}
.panel .pagebtns{{gap:6px}}
.panel .btn.pg{{padding:4px 10px; font-size:12px; line-height:1.4}}
.panel{{padding-bottom:10px}}          /* was 18px */
@media(max-width:760px){{
  .tablehint{{display:none}}           /* keep the pager on one line on phones */
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
      <button type="button" class="btn ghost" id="themeBtn">🌙 Theme</button>
      <button type="button" class="btn" id="csvBtn">⬇ CSV</button>
    </header>

    <div class="filterbar">
      <div class="fld"><label for="f-sup">Supplier</label><select id="f-sup" name="f-sup"></select></div>
      <div class="fld"><label for="f-cont">Container</label><select id="f-cont" name="f-cont"></select></div>
      <div class="fld"><label for="f-plat">Marketplace</label><select id="f-plat" name="f-plat"></select></div>
      <div class="fld"><label for="f-stat">Listing Status</label><select id="f-stat" name="f-stat">
        <option value="">All</option><option>Listed</option><option>Not Listed</option></select></div>
      <div class="fld"><label for="f-rfrom">Received from</label><div class="inp"><input type="date" id="f-rfrom" name="f-rfrom"></div></div>
      <div class="fld"><label for="f-rto">Received to</label><div class="inp"><input type="date" id="f-rto" name="f-rto"></div></div>
      <div class="fld"><label for="f-lfrom">Listed from</label><div class="inp"><input type="date" id="f-lfrom" name="f-lfrom"></div></div>
      <div class="fld"><label for="f-lto">Listed to</label><div class="inp"><input type="date" id="f-lto" name="f-lto"></div></div>
      <div class="fld grow"><label for="f-q">Search</label><div class="inp"><span class="inp-ic" aria-hidden="true">🔎</span>
        <input type="text" id="f-q" name="f-q" placeholder="SKU, supplier, container, PO, reason…"></div></div>
      <div class="fld"><span class="fld-spacer">&nbsp;</span><button type="button" class="tt-clear" id="clearBtn">Clear</button></div>
    </div>

    <div class="content">
      <div class="kpi-grid" id="kpi"></div>

      <div class="panel">
        <div class="phead">
          <div><h3>🗺️ Master Tracking Table <span class="muted">one Combo SKU × one marketplace per row</span></h3>
            <div class="sub">Component → Container → Combo → Listing → Traffic → Orders → Sales → Returns, in one view.
              <span class="muted" id="rowcount"></span></div></div>
          <div class="tablist" id="viewtabs">
            <button type="button" class="tab" data-view="comp">🧩 Components <b id="tabCompN"></b></button>
            <button type="button" class="tab active" data-view="combo">🎁 Combos <b id="tabComboN"></b></button>
          </div>
          <div class="perpage-wrap"><label for="perpage">Products</label>
            <select class="perpage" id="perpage" name="perpage" aria-label="Products per page"><option value="50">50</option><option value="100" selected>100</option><option value="250">250</option><option value="1000">1000</option><option value="0">All</option></select>
          </div>
        </div>
        <div class="tablewrap">
          <table id="tbl"><thead><tr id="thead"></tr></thead><tbody id="tbody"></tbody></table>
        </div>
        <div class="pageinfo">
          <div class="pginfo-left"><span id="pginfo"></span>
            <span class="tablehint">💡 Click any marketplace row to open the full record.</span></div>
          <div class="pagebtns">
            <button type="button" class="btn pg" id="prev">‹ Prev</button><span id="pgnum"></span><button type="button" class="btn pg" id="next">Next ›</button>
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
const B = PAYLOAD.B;
// Two independent datasets, identical column layout. Combos is the default view.
// Combos tab shows ONLY rows that have a combo. Components with no combo are listed on
// the Components tab; showing them here too duplicated them. They carry no marketplace
// or metrics, so no total changes. They are kept (NO_COMBO) only for the
// "No Combo Yet" KPI count.
const DATA = {{ combo: PAYLOAD.rows.filter(r=>r[B.bsku]), comp: PAYLOAD.rowsComp }};
const NO_COMBO = PAYLOAD.rows.filter(r=>!r[B.bsku]);
let VIEW = 'combo';
let ROWS = DATA[VIEW];
const COLS = {json.dumps(COLS)};
const PLABEL = {{amazon:'Amazon', ebay:'eBay', shopify:'Shopify', 'b&q':'B&Q', wayfair:'Wayfair', other:'Other'}};
// css-safe slug for the per-marketplace row tint ('b&q' is not a valid class name)
const PSLUG = {{amazon:'amazon', ebay:'ebay', shopify:'shopify', 'b&q':'bq', wayfair:'wayfair', other:'other'}};
const plSlug = p => PSLUG[p] || (p ? 'other' : 'none');

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

function filtered(list){{
  return (list || ROWS).filter(r=>{{
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
  // components with no combo, under the same filters/search as the table
  const noCombo = new Set(filtered(NO_COMBO).map(r=>r[B.csku]));
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

// Product-block cell.
// A combo built from several components shows EVERY component value stacked
// vertically inside the one cell -- no "+N", no extra rows, nothing hidden.
// comps entry: [0]=sku [1]=image [2]=created [3]=supplier [4]=container [5]=received
const COMP_IDX = {{csku:0, cimg:1, ccre:2, sup:3, cont:4, recv:5}};

function stackItem(val, type){{
  if(type==='img')
    return val ? `<img class="v2img" src="${{esc(val)}}" loading="lazy" referrerpolicy="no-referrer" alt="" onerror="this.outerHTML='&lt;div class=\\'v2noimg\\'&gt;🖼&lt;/div&gt;'">`
               : `<div class="v2noimg">—</div>`;
  if(type==='d') return val ? esc(fmtDate(val)) : '<span class="cell-mut">—</span>';
  if(!val)       return '<span class="cell-mut">—</span>';
  return `<span class="trunc" title="${{esc(val)}}">${{esc(val)}}</span>`;
}}

function prodCell(g, key, type){{
  const i = COMP_IDX[key];
  // Combo columns (bsku/bimg/bcre) are product-level -> single value, never stacked.
  if(i === undefined) return cell(g.head, key, type);
  const list = g.comps && g.comps.length ? g.comps : null;
  if(!list) return cell(g.head, key, type);
  if(list.length === 1) return stackItem(list[0][i], type);
  const vals = list.map(c=>c[i]);
  // If every component shares the same value (one supplier, one container, one
  // received date...) show it ONCE -- repeating it down the cell is duplication.
  // Only genuinely differing values are stacked.
  if(new Set(vals.map(v=>String(v==null?'':v))).size === 1)
    return stackItem(vals[0], type);
  return '<div class="pstack">' +
    vals.map(v=>`<div class="pitem">${{stackItem(v, type)}}</div>`).join('') +
    '</div>';
}}

// ---------- grouping: one PRODUCT, many MARKETPLACE rows ----------
// COLS[0..8]  = product columns  (rendered once, via rowspan)
// COLS[9..20] = marketplace columns (one row each)
const ALL_P = COLS.slice(0,9), ALL_M = COLS.slice(9);
// The TABLE shows only the essential columns (21 -> 11) so it stays scannable.
// Every hidden field is shown in the click-through drawer, nothing is lost.
// FULL original column set -- all 9 product + 12 marketplace columns are shown.
// The table scrolls horizontally AND vertically so every column stays reachable
// without changing the grouped layout. The drawer remains as a quick one-page
// read of a single record.
// Components tab: a component row never has a combo, so the three combo columns
// are always blank there -- hide them in that view only (Combos tab keeps all).
const COMBO_ONLY = ['bsku','bimg','bcre'];
const viewPCols = () => VIEW==='comp' ? ALL_P.filter(c=>!COMBO_ONLY.includes(c[1])) : ALL_P;
let PCOLS = viewPCols();
const MCOLS = ALL_M;
// Combos tab groups by Combo SKU, Components tab by Component SKU. In the combo
// view the metrics are keyed on the combo, so several component rows of the same
// combo carry identical numbers -- grouping removes that real duplication.
const RENDERED = [];   // render-order index -> {{row, group}} for the drawer
const groupKey = r => (VIEW==='combo' ? (r[B.bsku] || r[B.csku]) : r[B.csku]) || '—';

function groupRows(rs){{
  const m = new Map();
  for(const r of rs){{
    const k = groupKey(r);
    if(!m.has(k)) m.set(k, []);
    m.get(k).push(r);
  }}
  return [...m.values()].map(rows=>{{
    // B.comps carries every component behind this product as
    // [sku, image, created, supplier, container, received]. Older payloads stored
    // a bare SKU string or a [sku,image] pair -- pad those to the same shape so
    // the stacked cells always index safely.
    const norm = c => Array.isArray(c) ? c : [c];
    const seen = new Map();                       // de-dup by SKU, keep order
    for(const r of rows)
      for(const c of (r[B.comps] && r[B.comps].length ? r[B.comps] : [[r[B.csku]]])){{
        const a = norm(c); if(a[0] && !seen.has(a[0])) seen.set(a[0], a);
      }}
    const comps = [...seen.values()];
    return {{rows, head: rows[0], comps, cskus: comps.map(c=>c[0])}};
  }});
}}

// Default display priority (no column sort chosen): products with the most complete
// Container / Received Date first. Display order only -- values are untouched.
//   1 = Container and Received Date present, 2 = Container only, 3 = no Container.
// Uses the product row's own Container / Received Date fields (the same ones the
// filters read). Array.sort is stable, so each priority band keeps the original
// V2 payload order.
const dataPriority = g => g.head[B.cont] ? (g.head[B.recv] ? 1 : 2) : 3;

function sortGroups(gs){{
  if(!S.sort) return gs.sort((a,b)=>dataPriority(a)-dataPriority(b));
  const k = S.sort, t = (COLS.find(c=>c[1]===k)||['','','t'])[2];
  const isProd = k==='rid' || PCOLS.some(c=>c[1]===k);
  const val = g => {{
    if(k==='rid') return g.rows[0][B.rid] || '';
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
  PCOLS = viewPCols();
  const rs = filtered();
  kpis(rs);
  const groups = sortGroups(groupRows(rs));

  // header follows the VISIBLE column sets, not all 21
  const ridTh = `<th class="ridcol sortable${{S.sort==='rid'?' sorted':''}}" data-k="rid">Record ID`
      + `<span class="sarrow${{S.sort==='rid'?'':' dim'}}">${{S.sort==='rid'?(S.dir>0?'▲':'▼'):'⇅'}}</span></th>`;
  document.getElementById('thead').innerHTML = ridTh +
    PCOLS.concat(MCOLS).map(([lbl,key,t],i)=>{{
      const cls=['n','money','pct'].includes(t)?'num sortable':'sortable';
      const seg = i < PCOLS.length ? ' pcol' : ' mcol';
      const edge = i === PCOLS.length ? ' mstart' : '';
      const on = S.sort===key;
      return `<th class="${{cls}}${{seg}}${{edge}}${{on?' sorted':''}}" data-k="${{key}}">${{esc(lbl)}}<span class="sarrow${{on?'':' dim'}}">${{on?(S.dir>0?'▲':'▼'):'⇅'}}</span></th>`;
    }}).join('');

  // Pagination now counts PRODUCTS, not marketplace rows.
  const per   = S.per > 0 ? S.per : Math.max(groups.length, 1);
  const pages = Math.max(1, Math.ceil(groups.length/per));
  if(S.page>pages) S.page=pages;
  const slice = groups.slice((S.page-1)*per, S.page*per);

  let html = '', gi = 0;
  RENDERED.length = 0;
  for(const g of slice){{
    const n = g.rows.length, alt = (gi++ % 2) ? ' galt' : '';
    const gap = !g.head[B.bsku];
    g.rows.forEach((r, idx)=>{{
      const first = idx===0;
      const rix = RENDERED.length; RENDERED.push({{r, g}});
      html += `<tr data-ix="${{rix}}" class="grp${{alt}}${{first?' gfirst':''}}${{gap?' nocombo':''}} mk-${{plSlug(r[B.plat])}}"`
            + (first?` title="${{esc(g.head[B.notes]||'')}}"`:'') + '>';
      // Record ID is one per product -> written ONCE, spanning its marketplace rows
      // (same as the product columns), not repeated on every row.
      if(first) html += `<td class="ridcol" rowspan="${{n}}">${{esc(r[B.rid]||'')}}</td>`;
      if(first){{                                  // product block — rendered ONCE
        html += PCOLS.map(([lbl,key,t])=>{{
          const cls = (t==='img'?'imgcell ':'') + 'pcol';
          return `<td class="${{cls}}" rowspan="${{n}}">${{prodCell(g,key,t)}}</td>`;
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
    '<tr><td colspan="'+(1+PCOLS.length+MCOLS.length)+'" style="text-align:center;padding:40px;color:var(--muted)">No rows match these filters.</td></tr>';

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
// ---------- detail drawer: EVERY column for one record, on one page ----------
const fld = (label, val, cls='') =>
  `<div class="dfield ${{cls}}"><span class="dlabel">${{esc(label)}}</span><span class="dval ${{cls.includes('money')?'money':''}}">${{val}}</span></div>`;
const txt = v => (v===0 || v) && String(v).trim() !== '' ? esc(v) : '<span class="cell-mut">—</span>';
const dt  = v => v ? esc(fmtDate(v)) : '<span class="cell-mut">—</span>';
const pic = (url,label) => `<div class="dimg">${{url
  ? `<img src="${{esc(url)}}" loading="lazy" referrerpolicy="no-referrer" alt="" onerror="this.outerHTML='&lt;div class=\'v2noimg\'&gt;🖼&lt;/div&gt;'">`
  : '<div class="v2noimg">—</div>'}}<small>${{esc(label)}}</small></div>`;

function openDetail(ix){{
  const rec = RENDERED[ix]; if(!rec) return;
  const {{r, g}} = rec;
  const comps = (g.comps && g.comps.length) ? g.comps : [[r[B.csku]]];
  const isCombo = !!r[B.bsku];

  document.getElementById('dTitle').textContent = r[B.bsku] || r[B.csku] || '—';
  document.getElementById('dSub').innerHTML =
    `<span>${{isCombo?'🎁 Combo':'🧩 Component'}}</span><span class="dsep">·</span>` +
    `<span>${{esc(PLABEL[r[B.plat]] || r[B.plat] || 'No marketplace')}}</span><span class="dsep">·</span>` +
    (r[B.stat]==='Listed' ? '<span class="chip green">Listed</span>' : '<span class="chip gray">Not Listed</span>');

  // stack per-component values; collapse when every component shares one value
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
      <div class="dctitle">🚚 Supply chain</div>
      <div class="dgrid" style="grid-template-columns:1fr 1fr">
        ${{fld('Supplier',      stack(3))}}
        ${{fld('Container',     stack(4))}}
        ${{fld('Destination',   txt(r[B.dest]))}}
        ${{fld('Received Date', stack(5, dt))}}
        ${{fld('Purchase Order',txt(r[B.po]))}}
        ${{fld('Qty Received',  txt(num(r[B.qty]||0)))}}
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
        ${{fld('Impressions',       txt(num(r[B.impr]||0)))}}
        ${{fld('Clicks',            txt(num(r[B.clk]||0)))}}
        ${{fld('Orders',            txt(num(r[B.ord]||0)))}}
        ${{fld('Units Sold',        txt(num(r[B.units]||0)))}}
        ${{fld('Revenue',           money(r[B.rev]||0), 'money')}}
      </div>
    </div>

    <div class="dcard">
      <div class="dctitle">↩️ Returns &amp; feedback</div>
      <div class="dgrid" style="grid-template-columns:1fr 1fr">
        ${{fld('Total Returns',   txt(num(r[B.ret]||0)))}}
        ${{fld('Return Rate %',   `<span class="chip ${{rate>10?'red':rate>0?'orange':'gray'}}">${{rate.toFixed(2)}}%</span>`)}}
        ${{fld('Top Reason',      txt(r[B.reason]), 'wide')}}
        ${{fld('Average Feedback',cell(r,'fb','fb'), 'wide')}}
      </div>
    </div>

    ${{r[B.notes] ? `<div class="dcard span3"><div class="dctitle">📝 Notes</div>
        <div class="dval" style="font-weight:500;font-size:12.5px">${{esc(r[B.notes])}}</div></div>` : ''}}`;

  const bg = document.getElementById('drawerBg');
  bg.classList.remove('hidden');
  // Force a reflow, then add .open in the SAME tick. Doing this inside
  // requestAnimationFrame left the drawer at opacity:0 -- present and covering
  // the page (position:fixed; inset:0; z-index:80) but invisible, which also
  // swallowed every click on the dashboard behind it.
  void bg.offsetWidth;
  bg.classList.add('open');
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

document.getElementById('csvBtn').addEventListener('click',()=>{{
  const rs=filtered();
  const head=['Record ID'].concat(COLS.map(c=>c[0])).join(',');
  const body=rs.map(r=>[r[B.rid]||''].concat(COLS.map(([l,k,t])=>{{
    let v=r[B[k]];
    if(t==='fb') v = (v&&v.length) ? (Number(v[0]).toFixed(1)+'* ('+v[1]+' Reviews)') : 'No Reviews';
    const s=String(v==null?'':v);
    return /[",\\n]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s;
  }})).join(',')).join('\\n');
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
  if(v==='comp' && COMBO_ONLY.includes(S.sort)) S.sort = '';   // sorted column is hidden in this view
  buildFilterOpts();
  render();
}}
document.getElementById('viewtabs').addEventListener('click', e=>{{
  const t = e.target.closest('.tab[data-view]'); if(t) setView(t.dataset.view);
}});
document.getElementById('tabCompN').textContent  = '('+PAYLOAD.rowsComp.length+')';
document.getElementById('tabComboN').textContent = '('+DATA.combo.length+')';

buildFilterOpts();
render();
</script>
</body>
</html>
"""
out = PROJ/"dashboard-v2"/"index.html"
out.write_text(HTML, encoding="utf-8")
print(f"wrote {out}  ({out.stat().st_size:,} bytes)")
