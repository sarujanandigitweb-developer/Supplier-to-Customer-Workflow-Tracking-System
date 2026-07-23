/* Supplier-to-Customer Workflow Tracking — offline app.
   All KPIs/charts/tables are computed in JS from the raw arrays in data.js.
   The date range drives the business-rule lineage:
   New Components (created in range) -> their Combos -> Listings/Orders/Sales/Returns/Traffic. */
(function(){
  "use strict";
  var D=window.DASHBOARD_DATA, content=document.getElementById('content');

  /* column indices (see data.js meta.schema) */
  var CI={
    comp:{sku:0,desc:1,sup:2,po:3,cont:4,created:5,arr:6},
    combo:{sku:0,parts:1,first:2,listed:3},
    map:{comp:0,combo:1},
    list:{ref:0,sku:1,msku:2,ch:3,mkt:4,status:5,del:6,ended:7,wrong:8,date:9},
    ord:{oid:0,sku:1,src:2,mkt:3,status:4,date:5,qty:6,total:7},
    traf:{src:0,ref:1,ch:2,mkt:3,impr:4,clk:5},
    ret:{ch:0,oid:1,sku:2,date:3,reason:4,qty:5,refund:6},
    po:{po:0,supplier:1,code:2,order_date:3,container:4,cbm:5,arrived:6,confirmed:7,finished:8,expected:9}
  };

  /* ---- format helpers ---- */
  function n(x){ return (x==null?0:Math.round(x)).toLocaleString('en-GB'); }
  function money(x){ return '£'+(x||0).toLocaleString('en-GB',{maximumFractionDigits:0}); }
  function money2(x){ return '£'+(x||0).toLocaleString('en-GB',{minimumFractionDigits:2,maximumFractionDigits:2}); }
  function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
  function pct(a,b){ return b? ((a/b)*100).toFixed(1)+'%' : '—'; }
  function daysBetween(d){ if(!d) return 0; var t=new Date(D.meta.periodEnd)-new Date(d); return Math.max(0,Math.round(t/86400000)); }
  var CH_COLOR={amazon:'#ff9900',ebay:'#e53238',shopify:'#96bf48','B&Q':'#f28f1c'};

  /* ============================ DATE-DRIVEN COMPUTE ============================ */
  var FROM=D.meta.periodStart, TO=D.meta.periodEnd, ACT=null;
  function inRange(d){ return d && d>=FROM && d<=TO; }
  function compute(){
    var c=CI, compSet=Object.create(null), components=[];
    D.components.forEach(function(r){ if(inRange(r[c.comp.created])){ components.push(r); compSet[r[c.comp.sku]]=1; } });
    var comboSet=Object.create(null);
    D.componentComboMap.forEach(function(r){ if(compSet[r[c.map.comp]]) comboSet[r[c.map.combo]]=1; });
    var combos=D.combos.filter(function(r){ return comboSet[r[c.combo.sku]]; });
    var listings=D.listings.filter(function(r){ return comboSet[r[c.list.sku]]; });
    var refSet=Object.create(null); listings.forEach(function(r){ refSet[r[c.list.ref]]=1; });
    var traffic=D.traffic.filter(function(r){ return refSet[r[c.traf.ref]]; });
    var orders=D.orders.filter(function(r){ return comboSet[r[c.ord.sku]]; });
    var returns=D.returns.filter(function(r){ return comboSet[r[c.ret.sku]]; });
    // aggregation maps
    var comboOrders=Object.create(null);           // combo sku -> {orders:set, units, sales}
    orders.forEach(function(r){
      if(r[c.ord.status]!=='Completed') return;
      var k=r[c.ord.sku], o=comboOrders[k]||(comboOrders[k]={ord:Object.create(null),units:0,sales:0});
      o.ord[r[c.ord.oid]]=1; o.units+=r[c.ord.qty]; o.sales+=r[c.ord.total];
    });
    var compCombos=Object.create(null);            // component sku -> count of active combos
    D.componentComboMap.forEach(function(r){ if(compSet[r[c.map.comp]] && comboSet[r[c.map.combo]]){ (compCombos[r[c.map.comp]]=compCombos[r[c.map.comp]]||{}); compCombos[r[c.map.comp]][r[c.map.combo]]=1; } });
    var compMarkets=Object.create(null);           // component/combo sku -> set of channels (from listings)
    listings.forEach(function(r){ var k=r[c.list.sku]; (compMarkets[k]=compMarkets[k]||{})[r[c.list.ch]]=1; });
    var retBySku=Object.create(null);
    returns.forEach(function(r){ retBySku[r[c.ret.sku]]=(retBySku[r[c.ret.sku]]||0)+1; });
    ACT={components:components, compSet:compSet, combos:combos, comboSet:comboSet, listings:listings,
         traffic:traffic, orders:orders, returns:returns, comboOrders:comboOrders,
         compCombos:compCombos, compMarkets:compMarkets, retBySku:retBySku};
    return ACT;
  }

  /* ---- KPI helpers computed from ACT ---- */
  function ordersKPI(){
    var c=CI, oidset=Object.create(null), units=0, sales=0;
    ACT.orders.forEach(function(r){ if(r[c.ord.status]==='Completed'){ oidset[r[c.ord.oid]]=1; units+=r[c.ord.qty]; sales+=r[c.ord.total]; } });
    var orders=Object.keys(oidset).length;
    return {orders:orders, units:units, sales:sales, aov: orders? sales/orders : 0};
  }
  function listedSplit(){
    var c=CI, listed=0; ACT.combos.forEach(function(r){ if(r[c.combo.listed]===1) listed++; });
    return {listed:listed, non:ACT.combos.length-listed};
  }

  /* ============================ UI PRIMITIVES ============================ */
  function kpi(label,val,sub,tone,view,icon,note){
    icon=icon||'•'; var noteHtml=note?'<span class="kpi-note">'+esc(note)+'</span>':'';
    return '<div class="kpi k-'+(tone||'accent')+'"'+(view?' data-view="'+view+'"':'')+'>'+
      '<div class="kpi-top"><div class="kpi-ic">'+icon+'</div><div class="kpi-label">'+esc(label)+noteHtml+'</div></div>'+
      '<div class="val">'+val+'</div>'+(sub?'<div class="sub">'+esc(sub)+'</div>':'')+'</div>';
  }
  function chip(t,tone){ return '<span class="chip '+tone+'">'+esc(t)+'</span>'; }
  function statusChip(s){ var m={'Selling':'green','Listed':'blue','Has Combo':'orange','No Combo':'gray','Ended':'orange','Not Listed':'red'}; return chip(s,m[s]||'gray'); }

  function lineChart(series,opts){
    opts=opts||{}; if(!series.length) return '<div class="note">No data in range.</div>';
    var W=720,H=220,pad=38, max=Math.max.apply(null,series.map(function(p){return p.v;}))||1;
    var stepX=(W-pad*2)/(series.length-1||1);
    var pts=series.map(function(p,i){return [pad+i*stepX, H-pad-(p.v/max)*(H-pad*2)];});
    var path=pts.map(function(p,i){return (i?'L':'M')+p[0].toFixed(1)+' '+p[1].toFixed(1);}).join(' ');
    var area='M'+pad+' '+(H-pad)+' '+path.substring(1)+' L'+(pad+(series.length-1)*stepX)+' '+(H-pad)+' Z';
    var g=''; for(var k=0;k<=4;k++){var yy=pad+(H-pad*2)*k/4; g+='<line x1="'+pad+'" y1="'+yy+'" x2="'+(W-pad)+'" y2="'+yy+'" stroke="var(--line)"/>';}
    var lbl=series.map(function(p,i){return '<text x="'+(pad+i*stepX)+'" y="'+(H-12)+'" font-size="10" fill="var(--muted)" text-anchor="middle">'+esc(p.l.slice(2))+'</text>';}).join('');
    var dots=pts.map(function(p,i){return '<circle cx="'+p[0].toFixed(1)+'" cy="'+p[1].toFixed(1)+'" r="3" fill="var(--accent)"><title>'+esc(series[i].l)+': '+(opts.money?money(series[i].v):n(series[i].v))+'</title></circle>';}).join('');
    return '<svg class="chart" viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="none">'+g+'<path d="'+area+'" fill="rgba(47,111,237,.10)"/><path d="'+path+'" fill="none" stroke="var(--accent)" stroke-width="2.5"/>'+dots+lbl+'</svg>';
  }
  function miniBars(rows,colorFn){
    if(!rows.length) return '<div class="note">No data in range.</div>';
    var max=Math.max.apply(null,rows.map(function(r){return r.v;}))||1;
    return '<div class="mbar">'+rows.map(function(r){var c=colorFn?colorFn(r):'var(--accent)';
      return '<div class="row"><div>'+esc(r.l)+'</div><div class="track"><div class="fill" style="width:'+(r.v/max*100).toFixed(1)+'%;background:'+c+'"></div></div><div class="num">'+n(r.v)+'</div></div>';}).join('')+'</div>';
  }

  /* ---- sortable + paginated table (25/50/100/250/500) ---- */
  var PAGE={},PER={},PER_OPTS=[25,50,100,250,500],SORT={},RROWS={};
  function sNum(v){ v=+v; return isNaN(v)?null:v; }
  function sDate(v){ v=(v==null?'':String(v)); return /^\d{4}-\d{2}-\d{2}/.test(v)?v:null; }
  function tableP(id,cols,rows,opts){
    opts=opts||{}; var data=rows.slice(), srt=SORT[id];
    if(srt&&cols[srt.ci]&&cols[srt.ci].sort){ var acc=cols[srt.ci].sort,dir=srt.dir;
      data.sort(function(a,b){var va=acc(a),vb=acc(b); if(va==null&&vb==null)return 0; if(va==null)return 1; if(vb==null)return -1; return va<vb?-dir:va>vb?dir:0;}); }
    RROWS[id]=data;
    var per=(PER[id]!=null?PER[id]:(opts.per||25)); if(PAGE[id]==null)PAGE[id]=0;
    var pages=Math.max(1,Math.ceil(data.length/per)); if(PAGE[id]>=pages)PAGE[id]=0;
    var start=PAGE[id]*per, slice=data.slice(start,start+per);
    var thead='<tr>'+cols.map(function(c,ci){var so=!!c.sort,ac=srt&&srt.ci===ci;
      var ar=ac?'<span class="sarrow">'+(srt.dir>0?'▲':'▼')+'</span>':so?'<span class="sarrow dim">↕</span>':'';
      return '<th class="'+((c.num?'num ':'')+(so?'sortable':'')+(ac?' sorted':'')).trim()+'"'+(so?' data-sort-id="'+id+'" data-ci="'+ci+'"':'')+'>'+esc(c.t)+ar+'</th>';}).join('')+'</tr>';
    var body=slice.length?slice.map(function(r,i){return '<tr class="'+(opts.onRow?'clickable':'')+'" data-ri="'+(start+i)+'">'+cols.map(function(c){var v=c.render?c.render(r):r[c.k];return '<td class="'+(c.num?'num':'')+'">'+(v==null?'':v)+'</td>';}).join('')+'</tr>';}).join('')
      :'<tr><td colspan="'+cols.length+'" style="text-align:center;color:var(--muted);padding:26px">No matching rows.</td></tr>';
    var perSel=data.length>PER_OPTS[0]?'<label class="perpage-wrap">Rows per page <select class="perpage" data-id="'+id+'">'+PER_OPTS.map(function(v){return '<option'+(v==per?' selected':'')+'>'+v+'</option>';}).join('')+'</select></label>':'';
    var pager=pages>1?'<span class="pagebtns"><button type="button" class="btn pg" data-id="'+id+'" data-d="-1">‹ Prev</button><span>Page '+(PAGE[id]+1)+' / '+pages+'</span><button type="button" class="btn pg" data-id="'+id+'" data-d="1">Next ›</button></span>':'';
    var info='Showing '+(data.length?start+1:0)+'–'+Math.min(start+per,data.length)+' of '+n(data.length);
    return '<div class="tablewrap" data-tid="'+id+'"><table><thead>'+thead+'</thead><tbody>'+body+'</tbody></table></div><div class="pageinfo"><span class="pginfo-left">'+info+perSel+'</span>'+pager+'</div>';
  }
  function wireTable(){}   /* no-op: pagination/sort/row-clicks handled by event delegation */

  /* ---- per-table search toolbar ---- */
  var FILTERS={},REFOCUS=null;
  function gf(v){ return FILTERS[v]||(FILTERS[v]={q:''}); }
  function toolbar(view,ph,count){
    var f=gf(view);
    return '<div class="tabletools"><div class="tt-search"><span class="tt-ic">🔍</span><input class="tt-q" id="tt-'+view+'-q" placeholder="'+esc(ph||'Search…')+'" value="'+esc(f.q)+'" autocomplete="off"></div><span class="tt-spacer"></span>'+
      (count!=null?'<span class="tt-count">'+n(count)+' shown</span>':'')+
      '<button type="button" class="tt-clear" id="tt-'+view+'-clear">Clear</button></div>';
  }
  function wireToolbar(){}   /* no-op: search/clear handled by event delegation */
  function tablist(group,active,tabs){
    return '<div class="tablist" role="tablist">'+tabs.map(function(tb){
      return '<button type="button" class="tab'+(tb[0]===active?' active':'')+'" data-tab-group="'+group+'" data-tab="'+tb[0]+'" role="tab" aria-selected="'+(tb[0]===active)+'">'+esc(tb[1])+'</button>';
    }).join('')+'</div>';
  }
  function search(view,rows,fields){ var q=gf(view).q.trim().toUpperCase(); if(!q)return rows; return rows.filter(function(r){return fields(r).toUpperCase().indexOf(q)>=0;}); }

  /* ============================ VIEWS ============================ */
  var VIEWS={};
  var MKT_SEL='';   // Marketplace Status: selected channel ('' = All, default)
  var SALES_MKT=''; // Sales Performance: selected marketplace filter ('' = All)
  var TRAFFIC_MKT=''; // Traffic: selected marketplace/channel ('' = All, default)
  var TRAFFIC_SRC=''; // Traffic: selected source ('' = All, 'organic', 'paid')
  var RETURNS_MKT=''; // Returns: selected marketplace/channel ('' = All, default)
  var SALES_TAB='order';     // Sales Performance: 'order' | 'sku'
  var RETURNS_TAB='platform'; // Returns: 'platform' | 'sku'
  var SUPPLIERS_TAB='supplier'; // Supplier & Container: 'supplier' | 'po'

  VIEWS.dashboard=function(){
    var ok=ordersKPI(), ls=listedSplit(), c=CI;
    var cards=kpi('New Components',n(ACT.components.length),'created in range','green','journey','📦')
      +kpi('New Combo SKUs',n(ACT.combos.length),'from new components','blue','combos','🧩')
      +kpi('Listed Combo SKUs',n(ls.listed),pct(ls.listed,ACT.combos.length)+' listed','green','marketplace','✅')
      +kpi('Orders',n(ok.orders),n(ok.units)+' units','accent','sales','🛒')
      +kpi('Sales',money(ok.sales),'AOV '+money2(ok.aov),'red','sales','💷')
      +kpi('Returns',n(ACT.returns.length),'in range','red','returns','↩️');
    // funnel
    var poSet={},contSet={},supSet={};
    ACT.components.forEach(function(r){ if(r[c.comp.po])poSet[r[c.comp.po]]=1; if(r[c.comp.cont])contSet[r[c.comp.cont]]=1; if(r[c.comp.sup])supSet[r[c.comp.sup]]=1; });
    var funnel=[['Suppliers',Object.keys(supSet).length,'suppliers'],['Purchase Orders',Object.keys(poSet).length,'suppliers'],['Containers',Object.keys(contSet).length,'suppliers'],['Components',ACT.components.length,'journey'],['Combos',ACT.combos.length,'combos'],['Listed',ls.listed,'marketplace'],['Orders',ok.orders,'sales'],['Returns',ACT.returns.length,'returns']];
    var fmax=Math.max.apply(null,funnel.map(function(f){return f[1];}))||1;
    var fico={Suppliers:'🏭','Purchase Orders':'📄',Containers:'🚢',Components:'📦',Combos:'🧩',Listed:'✅',Orders:'🛒',Returns:'↩️'};
    var fH='<div class="funnel-h">'+funnel.map(function(f,i){return (i?'<div class="farrow">→</div>':'')+'<div class="fnode '+(f[1]>0?'ok':'nodata')+'" data-view="'+f[2]+'"><div class="fcircle">'+fico[f[0]]+'</div><div class="fname">'+f[0]+'</div><div class="fval">'+n(f[1])+'</div></div>';}).join('')+'</div>';
    // sales trend by month
    var trend=monthly(ACT.orders); var salesS=trend.map(function(m){return {l:m.month,v:m.sales};});
    // marketplace distribution
    var mk=byKey(ACT.listings,c.list.ch); var mkRows=Object.keys(mk).map(function(k){return {l:k,v:mk[k]};}).sort(function(a,b){return b.v-a.v;});
    // summary table 1: top selling combos
    var topCombos=ACT.combos.map(function(r){var k=r[c.combo.sku],co=ACT.comboOrders[k];return {sku:k,orders:co?Object.keys(co.ord).length:0,sales:co?co.sales:0};}).filter(function(r){return r.sales>0;}).sort(function(a,b){return b.sales-a.sales;}).slice(0,8);
    var topComboTable=tableP('dashTopCombo',[
      {t:'Combo SKU',render:function(r){return '<b>'+esc(r.sku)+'</b>';}},
      {t:'Orders',num:true,render:function(r){return n(r.orders);}},
      {t:'Sales',num:true,render:function(r){return money(r.sales);}}
    ],topCombos,{per:8,perPage:false});
    // summary table 2: sales by marketplace (Completed)
    var mkSales={}; ACT.orders.forEach(function(r){ if(r[c.ord.status]!=='Completed')return; var k=r[c.ord.src]||'—'; var a=mkSales[k]||(mkSales[k]={ord:{},sales:0}); a.ord[r[c.ord.oid]]=1; a.sales+=r[c.ord.total]; });
    var mkSalesRows=Object.keys(mkSales).map(function(k){return {mkt:k,orders:Object.keys(mkSales[k].ord).length,sales:mkSales[k].sales};}).sort(function(a,b){return b.sales-a.sales;});
    var mkSalesTable=tableP('dashMktSales',[
      {t:'Marketplace',render:function(r){return '<b>'+esc(r.mkt)+'</b>';}},
      {t:'Orders',num:true,render:function(r){return n(r.orders);}},
      {t:'Revenue',num:true,render:function(r){return money(r.sales);}},
      {t:'% Rev',num:true,render:function(r){return pct(r.sales,ok.sales);}}
    ],mkSalesRows,{per:12,perPage:false});
    return '<div class="kpi-grid">'+cards+'</div>'+
      '<div class="panel"><div class="phead"><div><h3>🚦 Journey Funnel <span class="muted">— New Component → … → Returns</span></h3></div></div>'+fH+'</div>'+
      '<div class="grid-2">'+
        '<div class="panel"><h3>📈 Sales Trend <span class="muted">— by month</span></h3>'+lineChart(salesS,{money:true})+'</div>'+
        '<div class="panel"><h3>🌍 Marketplace Distribution <span class="muted">— listings</span></h3>'+miniBars(mkRows,function(r){return CH_COLOR[r.l]||'var(--accent)';})+'</div>'+
      '</div>'+
      '<div class="grid-2">'+
        '<div class="panel"><h3>🏆 Top Selling Combos <span class="muted">— by revenue</span></h3>'+topComboTable+'</div>'+
        '<div class="panel"><h3>🛒 Sales by Marketplace</h3>'+mkSalesTable+'</div>'+
      '</div>';
  };

  function monthly(orders){
    var c=CI, m={};
    orders.forEach(function(r){ if(r[c.ord.status]!=='Completed')return; var mo=r[c.ord.date].slice(0,7); var o=m[mo]||(m[mo]={orders:{},sales:0,units:0}); o.orders[r[c.ord.oid]]=1; o.sales+=r[c.ord.total]; o.units+=r[c.ord.qty]; });
    return Object.keys(m).sort().map(function(k){return {month:k,orders:Object.keys(m[k].orders).length,sales:m[k].sales,units:m[k].units};});
  }
  function byKey(rows,idx){ var m={}; rows.forEach(function(r){ var k=r[idx]||'—'; m[k]=(m[k]||0)+1; }); return m; }

  VIEWS.journey=function(){
    var c=CI;
    var rows=ACT.components.map(function(r){
      var sku=r[c.comp.sku];
      var combos=ACT.compCombos[sku]?Object.keys(ACT.compCombos[sku]).length:0;
      var markets=ACT.compMarkets[sku]?Object.keys(ACT.compMarkets[sku]).length:0;
      var status=combos>0&&markets>0?'Selling':markets>0?'Listed':combos>0?'Has Combo':'No Combo';
      return {sku:sku,desc:r[c.comp.desc],sup:r[c.comp.sup],po:r[c.comp.po],cont:r[c.comp.cont],created:r[c.comp.created],combos:combos,markets:markets,status:status};
    });
    rows=search('journey',rows,function(r){return r.sku+' '+r.desc+' '+r.sup+' '+r.po+' '+r.cont;});
    var t=tableP('journey',[
      {t:'Component SKU',render:function(r){return '<b>'+esc(r.sku)+'</b>';}},
      {t:'Description',render:function(r){return esc(r.desc);}},
      {t:'Supplier',render:function(r){return esc(r.sup);}},
      {t:'PO',render:function(r){return esc(r.po);}},
      {t:'Container',render:function(r){return r.cont?esc(r.cont):chip('—','gray');}},
      {t:'Created',sort:function(r){return sDate(r.created);},render:function(r){return esc(r.created);}},
      {t:'Combos',num:true,sort:function(r){return r.combos;},render:function(r){return n(r.combos);}},
      {t:'Markets',num:true,sort:function(r){return r.markets;},render:function(r){return r.markets>0?chip('Listed ('+r.markets+')','green'):chip('Not Listed','gray');}},
      {t:'Status',render:function(r){return statusChip(r.status);}}
    ],rows,{per:25});
    setTimeout(function(){wireToolbar('journey');wireTable('journey',null,function(){render('journey');});},0);
    return sect('📦 Component Journey','New components created between '+FROM+' and '+TO+'. Click column headers to sort.')+
      '<div class="panel">'+toolbar('journey','Search SKU, description, supplier, PO…',rows.length)+t+'</div>';
  };

  VIEWS.combos=function(){
    var c=CI, ls=listedSplit();
    var avg=ACT.combos.length?(ACT.combos.reduce(function(a,r){return a+r[c.combo.parts];},0)/ACT.combos.length):0;
    var cards=kpi('Combo SKUs',n(ACT.combos.length),'from new components','blue','','🧩')
      +kpi('Listed',n(ls.listed),pct(ls.listed,ACT.combos.length),'green')
      +kpi('Non-Listed',n(ls.non),'','orange')
      +kpi('Avg Components / Combo',avg.toFixed(1),'','accent');
    var rows=ACT.combos.map(function(r){var k=r[c.combo.sku],co=ACT.comboOrders[k];return {sku:k,parts:r[c.combo.parts],first:r[c.combo.first],listed:r[c.combo.listed],orders:co?Object.keys(co.ord).length:0,sales:co?co.sales:0,ret:ACT.retBySku[k]||0};});
    rows=search('combos',rows,function(r){return r.sku;});
    var t=tableP('combos',[
      {t:'Combo SKU',render:function(r){return '<b>'+esc(r.sku)+'</b>';}},
      {t:'Parent Components',render:function(r){return esc(r.sku.split('+').join(' + '));}},
      {t:'First Listed',sort:function(r){return sDate(r.first);},render:function(r){return r.first||'—';}},
      {t:'Listed',render:function(r){return r.listed?chip('Yes','green'):chip('No','red');}},
      {t:'Orders',num:true,sort:function(r){return r.orders;},render:function(r){return n(r.orders);}},
      {t:'Sales',num:true,sort:function(r){return r.sales;},render:function(r){return money(r.sales);}},
      {t:'Returns',num:true,sort:function(r){return r.ret;},render:function(r){return r.ret?n(r.ret):'—';}}
    ],rows,{per:25});
    setTimeout(function(){wireToolbar('combos');wireTable('combos',null,function(){render('combos');});},0);
    return sect('🧩 Combo Creation','All combos built from components created in the selected period.')+
      '<div class="kpi-grid">'+cards+'</div><div class="panel"><h3>Combo SKUs</h3>'+toolbar('combos','Search combo SKU or component…',rows.length)+t+'</div>';
  };

  VIEWS.marketplace=function(){
    var c=CI, mk=byKey(ACT.listings,c.list.ch);
    var channels=Object.keys(mk).sort(function(a,b){return mk[b]-mk[a];});
    var total=ACT.listings.length;
    if(MKT_SEL && channels.indexOf(MKT_SEL)<0) MKT_SEL='';   // reset if selection not present in range
    var sel=MKT_SEL, CH_ICON={amazon:'🛒',ebay:'🏷️',shopify:'🛍️','B&Q':'🔧',wayfair:'🛋️'};
    function mcard(key,label,icon,cnt){
      return '<div class="kpi mktcard'+(key===sel?' active':'')+'" data-mkt="'+esc(key)+'" role="button" tabindex="0" aria-pressed="'+(key===sel)+'">'+
        '<div class="kpi-top"><div class="kpi-ic">'+icon+'</div><div class="kpi-label">'+esc(label)+'</div></div>'+
        '<div class="val">'+n(cnt)+'</div><div class="sub">listings</div></div>';
    }
    var cards=mcard('','All','🌐',total)+channels.map(function(k){return mcard(k,k,CH_ICON[k]||'🌍',mk[k]);}).join('');
    if(!channels.length) cards='<div class="note">No listings for the selected period.</div>';
    // filter the dataset by the selected marketplace (All = no filter)
    var base = sel ? ACT.listings.filter(function(r){return r[c.list.ch]===sel;}) : ACT.listings;
    var rows=base.map(function(r){return {sku:r[c.list.sku],ch:r[c.list.ch],mkt:r[c.list.mkt],status:(r[c.list.ended]||r[c.list.del])?'Ended':'Listed',date:r[c.list.date],days:daysBetween(r[c.list.date]),wrong:r[c.list.wrong],ended:r[c.list.ended]};});
    rows=search('marketplace',rows,function(r){return r.sku+' '+r.ch+' '+r.mkt;});
    var t=tableP('mkt',[
      {t:'SKU',render:function(r){return '<b>'+esc(r.sku)+'</b>';}},
      {t:'Marketplace',render:function(r){return esc(r.ch)+' · '+esc(r.mkt);}},
      {t:'Status',render:function(r){return statusChip(r.status);}},
      {t:'Listing Date',sort:function(r){return sDate(r.date);},render:function(r){return esc(r.date);}},
      {t:'Days Live',num:true,sort:function(r){return r.days;},render:function(r){return n(r.days);}},
      {t:'Wrong SKU',render:function(r){return r.wrong?chip('Yes','red'):chip('No','green');}},
      {t:'Ended',render:function(r){return r.ended?chip('Yes','orange'):chip('No','gray');}}
    ],rows,{per:25});
    var selLabel = sel ? esc(sel) : 'All marketplaces';
    return sect('🌍 Marketplace Status','Listings for the qualifying combos in the selected period. Showing: '+selLabel+'.')+
      '<div class="kpi-grid">'+cards+'</div><div class="panel"><h3>Listings <span class="muted">— '+selLabel+'</span></h3>'+toolbar('marketplace','Search SKU or marketplace…',rows.length)+t+'</div>';
  };

  VIEWS.sales=function(){
    var c=CI, ok=ordersKPI();
    var cards=kpi('Orders',n(ok.orders),'Completed','accent','','🛒')+kpi('Revenue',money(ok.sales),'','green','','💷')+kpi('Units',n(ok.units),'','blue','','📦')+kpi('Avg Order Value',money2(ok.aov),'','blue','','🧾')+kpi('Returns',n(ACT.returns.length),pct(ACT.returns.length,ok.orders)+' of orders','red','returns','↩️');
    var trend=monthly(ACT.orders);
    // sales by marketplace (platform) — Completed orders grouped by source_name
    var byMkt={};
    ACT.orders.forEach(function(r){ if(r[c.ord.status]!=='Completed') return; var k=(r[c.ord.src]||'—'); var o=byMkt[k]||(byMkt[k]={ord:{},units:0,sales:0}); o.ord[r[c.ord.oid]]=1; o.units+=r[c.ord.qty]; o.sales+=r[c.ord.total]; });
    var mrows=Object.keys(byMkt).map(function(k){return {mkt:k,orders:Object.keys(byMkt[k].ord).length,units:byMkt[k].units,sales:byMkt[k].sales};}).sort(function(a,b){return b.sales-a.sales;});
    var totSales=ok.sales;
    var mktBars=miniBars(mrows.map(function(r){return {l:r.mkt,v:r.sales};}),function(r){return CH_COLOR[String(r.l).toLowerCase()]||'var(--accent)';});
    var mktTable=tableP('salesmkt',[
      {t:'Marketplace',render:function(r){return '<b>'+esc(r.mkt)+'</b>';}},
      {t:'Orders',num:true,sort:function(r){return r.orders;},render:function(r){return n(r.orders);}},
      {t:'Units',num:true,sort:function(r){return r.units;},render:function(r){return n(r.units);}},
      {t:'Revenue',num:true,sort:function(r){return r.sales;},render:function(r){return money(r.sales);}},
      {t:'% of Revenue',num:true,sort:function(r){return r.sales;},render:function(r){return pct(r.sales,totSales);}}
    ],mrows,{per:25,perPage:false});
    // ORDER DETAILS — rich order-level columns, filterable by marketplace + search
    var mkts=Object.keys(byMkt).sort();
    var f=gf('sales'), q=f.q.trim().toUpperCase();
    var od=ACT.orders.filter(function(r){ return !SALES_MKT || r[c.ord.src]===SALES_MKT; });
    if(q) od=od.filter(function(r){ return (r[c.ord.oid]+' '+r[c.ord.sku]+' '+r[c.ord.src]+' '+r[c.ord.mkt]+' '+r[c.ord.status]).toUpperCase().indexOf(q)>=0; });
    function ostatus(s){ var t=String(s).toLowerCase(), tone=t==='completed'?'green':t.indexOf('cancel')>=0?'red':(t.indexOf('refund')>=0||t.indexOf('return')>=0?'orange':'gray'); return chip(s||'—',tone); }
    var odTable=tableP('orders',[
      {t:'Order ID',render:function(r){return '<b>'+esc(r[c.ord.oid])+'</b>';}},
      {t:'Order Date',sort:function(r){return sDate(r[c.ord.date]);},render:function(r){return esc(r[c.ord.date]);}},
      {t:'SKU',render:function(r){return esc(r[c.ord.sku]);}},
      {t:'Marketplace',render:function(r){return esc(r[c.ord.src]);}},
      {t:'Country',render:function(r){return esc(r[c.ord.mkt]);}},
      {t:'Status',render:function(r){return ostatus(r[c.ord.status]);}},
      {t:'Units',num:true,sort:function(r){return r[c.ord.qty];},render:function(r){return n(r[c.ord.qty]);}},
      {t:'Order Total',num:true,sort:function(r){return r[c.ord.total];},render:function(r){return money2(r[c.ord.total]);}}
    ],od,{per:25});
    // SKU-WISE aggregation (Completed, respecting the marketplace filter)
    var skuAgg={};
    ACT.orders.forEach(function(r){ if(r[c.ord.status]!=='Completed')return; if(SALES_MKT&&r[c.ord.src]!==SALES_MKT)return;
      var k=r[c.ord.sku]; var a=skuAgg[k]||(skuAgg[k]={sku:k,ord:{},mk:{},units:0,sales:0});
      a.ord[r[c.ord.oid]]=1; a.mk[r[c.ord.src]]=1; a.units+=r[c.ord.qty]; a.sales+=r[c.ord.total]; });
    var skuRows=Object.keys(skuAgg).map(function(k){var a=skuAgg[k],o=Object.keys(a.ord).length;return {sku:k,orders:o,units:a.units,sales:a.sales,aov:o?a.sales/o:0,mk:Object.keys(a.mk).length};});
    if(q) skuRows=skuRows.filter(function(r){return r.sku.toUpperCase().indexOf(q)>=0;});
    var skuTable=tableP('salessku',[
      {t:'SKU',render:function(r){return '<b>'+esc(r.sku)+'</b>';}},
      {t:'Marketplaces',num:true,sort:function(r){return r.mk;},render:function(r){return n(r.mk);}},
      {t:'Orders',num:true,sort:function(r){return r.orders;},render:function(r){return n(r.orders);}},
      {t:'Units',num:true,sort:function(r){return r.units;},render:function(r){return n(r.units);}},
      {t:'Revenue',num:true,sort:function(r){return r.sales;},render:function(r){return money(r.sales);}},
      {t:'Avg Order Value',num:true,sort:function(r){return r.aov;},render:function(r){return money2(r.aov);}}
    ],skuRows,{per:25});
    var isSku=(SALES_TAB==='sku');
    var salesTools='<div class="tabletools"><div class="tt-search"><span class="tt-ic">🔍</span>'+
      '<input class="tt-q" id="tt-sales-q" placeholder="'+(isSku?'Search SKU…':'Search order ID, SKU, status…')+'" value="'+esc(f.q)+'" autocomplete="off"></div>'+
      '<select class="tt-select" id="tt-sales-mkt" title="Marketplace"><option value="">All marketplaces</option>'+
        mkts.map(function(m){return '<option'+(m===SALES_MKT?' selected':'')+'>'+esc(m)+'</option>';}).join('')+'</select>'+
      '<span class="tt-spacer"></span><span class="tt-count">'+n(isSku?skuRows.length:od.length)+' '+(isSku?'SKUs':'orders')+'</span>'+
      '<button type="button" class="tt-clear" id="tt-sales-clear">Clear</button></div>';
    return sect('📈 Sales Performance','Orders / Sales for qualifying combo SKUs (Completed).')+
      '<div class="kpi-grid">'+cards+'</div>'+
      '<div class="grid-2"><div class="panel"><h3>Sales Trend</h3>'+lineChart(trend.map(function(m){return {l:m.month,v:m.sales};}),{money:true})+'</div><div class="panel"><h3>Orders Trend</h3>'+lineChart(trend.map(function(m){return {l:m.month,v:m.orders};}),{})+'</div></div>'+
      '<div class="grid-2"><div class="panel"><h3>💷 Revenue by Marketplace</h3>'+mktBars+'</div><div class="panel"><h3>🛒 Sales by Marketplace</h3>'+mktTable+'</div></div>'+
      '<div class="panel"><div class="phead"><div><h3>'+(isSku?'🏷️ SKU-wise Sales':'🧾 Order Details')+(SALES_MKT?' <span class="muted">— '+esc(SALES_MKT)+'</span>':'')+'</h3></div>'+tablist('sales',SALES_TAB,[['order','Order-wise'],['sku','SKU-wise']])+'</div>'+salesTools+(isSku?skuTable:odTable)+'</div>';
  };

  VIEWS.traffic=function(){
    var c=CI, base=ACT.traffic;
    // ---- Marketplace (channel) options for the filter dropdown ----
    var byCh={}; base.forEach(function(r){var k=r[c.traf.ch]||'—'; byCh[k]=(byCh[k]||0)+r[c.traf.impr];});
    var channels=Object.keys(byCh).sort(function(a,b){return byCh[b]-byCh[a];});
    if(TRAFFIC_MKT && channels.indexOf(TRAFFIC_MKT)<0) TRAFFIC_MKT='';
    var selMkt=TRAFFIC_MKT;
    var scoped = selMkt ? base.filter(function(r){return r[c.traf.ch]===selMkt;}) : base;  // drives KPIs + charts + table
    // ---- KPI cards (respect selected marketplace) ----
    var org={i:0,cl:0},paid={i:0,cl:0};
    scoped.forEach(function(r){var t=r[c.traf.src]==='paid'?paid:org;t.i+=r[c.traf.impr];t.cl+=r[c.traf.clk];});
    var ti=org.i+paid.i, tc=org.cl+paid.cl;
    var cards=kpi('Impressions',n(ti),'organic + paid','accent','','👁️')+kpi('Clicks',n(tc),'','blue','','🖱️')+kpi('CTR',pct(tc,ti),'clicks ÷ impressions','green','','🎯')+kpi('Organic',n(org.i),pct(org.cl,org.i)+' CTR','gray','','🌱')+kpi('PPC / Paid',n(paid.i),pct(paid.cl,paid.i)+' CTR','orange','','💰');
    // ---- charts (respect selected marketplace) ----
    var byCtry={}; scoped.forEach(function(r){var k=r[c.traf.mkt]||'—';byCtry[k]=(byCtry[k]||0)+r[c.traf.impr];});
    var ctryRows=Object.keys(byCtry).map(function(k){return {l:k,v:byCtry[k]};}).sort(function(a,b){return b.v-a.v;});
    var srcRows=[{l:'Organic',v:org.i},{l:'PPC / Paid',v:paid.i}];
    // ---- table: raw source-level records (Source column preserved) + Source filter + search ----
    var srcSel=TRAFFIC_SRC, f=gf('traffic'), q=f.q.trim().toUpperCase();
    var rows=scoped.filter(function(r){return !srcSel || r[c.traf.src]===srcSel;});
    if(q) rows=rows.filter(function(r){return (r[c.traf.ref]+' '+r[c.traf.ch]+' '+r[c.traf.mkt]+' '+r[c.traf.src]).toUpperCase().indexOf(q)>=0;});
    function srcChip(s){return s==='paid'?chip('PPC','orange'):chip('Organic','green');}
    var t=tableP('traf',[
      {t:'Source',sort:function(r){return r[c.traf.src];},render:function(r){return srcChip(r[c.traf.src]);}},
      {t:'Listing (ref_id)',render:function(r){return '<b>'+esc(r[c.traf.ref])+'</b>';}},
      {t:'Channel',render:function(r){return esc(r[c.traf.ch]);}},
      {t:'Marketplace',render:function(r){return esc(r[c.traf.mkt]);}},
      {t:'Impressions',num:true,sort:function(r){return r[c.traf.impr];},render:function(r){return n(r[c.traf.impr]);}},
      {t:'Clicks',num:true,sort:function(r){return r[c.traf.clk];},render:function(r){return n(r[c.traf.clk]);}},
      {t:'CTR',num:true,sort:function(r){return r[c.traf.impr]?r[c.traf.clk]/r[c.traf.impr]:0;},render:function(r){return pct(r[c.traf.clk],r[c.traf.impr]);}}
    ],rows,{per:25});
    var tools='<div class="tabletools"><div class="tt-search"><span class="tt-ic">🔍</span>'+
      '<input class="tt-q" id="tt-traffic-q" placeholder="Search ref_id, channel, marketplace…" value="'+esc(f.q)+'" autocomplete="off"></div>'+
      '<select class="tt-select" id="tt-traffic-mkt" title="Marketplace"><option value="">All marketplaces</option>'+
        channels.map(function(k){return '<option'+(k===selMkt?' selected':'')+'>'+esc(k)+'</option>';}).join('')+'</select>'+
      '<select class="tt-select" id="tt-traffic-src" title="Traffic Source"><option value="">All sources</option>'+
        '<option value="organic"'+(srcSel==='organic'?' selected':'')+'>Organic</option>'+
        '<option value="paid"'+(srcSel==='paid'?' selected':'')+'>PPC / Paid</option></select>'+
      '<span class="tt-spacer"></span><span class="tt-count">'+n(rows.length)+' records</span>'+
      '<button type="button" class="tt-clear" id="tt-traffic-clear">Clear</button></div>';
    var selLabel=selMkt?esc(selMkt):'All marketplaces';
    return sect('🚦 Traffic','traffic_data (organic) + ppc_performance (paid), reconnected to combos via listing_data. Showing: '+selLabel+'.')+
      '<div class="kpi-grid">'+cards+'</div>'+
      '<div class="grid-2"><div class="panel"><h3>👁️ Impressions by Marketplace (country)</h3>'+miniBars(ctryRows,function(){return 'var(--accent)';})+'</div><div class="panel"><h3>🌱 Organic vs PPC <span class="muted">— impressions</span></h3>'+miniBars(srcRows,function(r){return r.l==='Organic'?'var(--green)':'var(--orange)';})+'</div></div>'+
      '<div class="panel"><h3>📄 Traffic Records'+(selMkt?' <span class="muted">— '+esc(selMkt)+'</span>':'')+'</h3>'+tools+t+'</div>';
  };

  VIEWS.returns=function(){
    var c=CI;
    // channel breakdown (overview KPIs + bars) — full, unaffected by the marketplace filter
    var ch={}, totUnits=0, totRefund=0;
    ACT.returns.forEach(function(r){var k=r[c.ret.ch]; var a=ch[k]||(ch[k]={lines:0,qty:0,refund:0}); a.lines++; a.qty+=(r[c.ret.qty]||0); a.refund+=(r[c.ret.refund]||0); totUnits+=(r[c.ret.qty]||0); totRefund+=(r[c.ret.refund]||0);});
    var cards=kpi('Total Returns',n(ACT.returns.length),n(totUnits)+' units','red','','↩️')
      +kpi('Amazon',n((ch.amazon||{}).lines||0),n((ch.amazon||{}).qty||0)+' units · '+money((ch.amazon||{}).refund||0),'orange','','🛒')
      +kpi('eBay',n((ch.ebay||{}).lines||0),n((ch.ebay||{}).qty||0)+' units · '+money((ch.ebay||{}).refund||0),'orange','','🏷️')
      +kpi('Shopify',n((ch.shopify||{}).lines||0),n((ch.shopify||{}).qty||0)+' units · '+money((ch.shopify||{}).refund||0),'gray','','🛍️')
      +kpi('Refund Value',money(totRefund),'buyer refunds','blue','','💷');
    var barRows=['amazon','ebay','shopify'].map(function(k){return {l:k,v:(ch[k]||{}).lines||0};}).filter(function(r){return r.v>0;});
    // marketplace filter options
    var channels=Object.keys(ch).sort(function(a,b){return ch[b].lines-ch[a].lines;});
    if(RETURNS_MKT && channels.indexOf(RETURNS_MKT)<0) RETURNS_MKT='';
    var selMkt=RETURNS_MKT;
    // DETAIL records (raw rows) filtered by marketplace + search
    var f=gf('returns'), q=f.q.trim().toUpperCase();
    var rows=ACT.returns.filter(function(r){return !selMkt || r[c.ret.ch]===selMkt;});
    if(q) rows=rows.filter(function(r){return (r[c.ret.ch]+' '+r[c.ret.oid]+' '+r[c.ret.sku]+' '+(r[c.ret.reason]||'')).toUpperCase().indexOf(q)>=0;});
    function chChip(k){var m={amazon:'orange',ebay:'blue',shopify:'green'};return chip(k,m[k]||'gray');}
    function cleanReason(x){return x?esc(String(x).replace('CR-','').replace('AMZ-PG-','')):chip('—','gray');}
    var t=tableP('ret',[
      {t:'Marketplace',sort:function(r){return r[c.ret.ch];},render:function(r){return chChip(r[c.ret.ch]);}},
      {t:'Order ID',render:function(r){return '<b>'+esc(r[c.ret.oid])+'</b>';}},
      {t:'Combo SKU',render:function(r){return esc(r[c.ret.sku]);}},
      {t:'Return Date',sort:function(r){return sDate(r[c.ret.date]);},render:function(r){return esc(r[c.ret.date]);}},
      {t:'Reason',render:function(r){return cleanReason(r[c.ret.reason]);}},
      {t:'Qty',num:true,sort:function(r){return r[c.ret.qty]==null?-1:r[c.ret.qty];},render:function(r){return r[c.ret.qty]==null?chip('—','gray'):n(r[c.ret.qty]);}},
      {t:'Refund',num:true,sort:function(r){return r[c.ret.refund]==null?-1:r[c.ret.refund];},render:function(r){return r[c.ret.refund]==null?'—':money2(r[c.ret.refund]);}}
    ],rows,{per:25});
    // SKU-WISE aggregation (respecting the marketplace filter): product return count + related data
    var sAgg={};
    ACT.returns.forEach(function(r){ if(selMkt && r[c.ret.ch]!==selMkt) return;
      var k=r[c.ret.sku]; var a=sAgg[k]||(sAgg[k]={sku:k,count:0,units:0,refund:0,ch:{},reason:{}});
      a.count++; a.units+=(r[c.ret.qty]||0); a.refund+=(r[c.ret.refund]||0); a.ch[r[c.ret.ch]]=1;
      if(r[c.ret.reason])a.reason[r[c.ret.reason]]=(a.reason[r[c.ret.reason]]||0)+1; });
    var sRows=Object.keys(sAgg).map(function(k){var a=sAgg[k];
      var top=Object.keys(a.reason).sort(function(x,y){return a.reason[y]-a.reason[x];})[0];
      return {sku:k,count:a.count,units:a.units,refund:a.refund,channels:Object.keys(a.ch).sort().join(', '),topReason:top||null};});
    if(q) sRows=sRows.filter(function(r){return r.sku.toUpperCase().indexOf(q)>=0;});
    var skuTable=tableP('retsku',[
      {t:'Combo SKU',render:function(r){return '<b>'+esc(r.sku)+'</b>';}},
      {t:'Channels',render:function(r){return esc(r.channels);}},
      {t:'Return Count',num:true,sort:function(r){return r.count;},render:function(r){return n(r.count);}},
      {t:'Units',num:true,sort:function(r){return r.units;},render:function(r){return n(r.units);}},
      {t:'Refund',num:true,sort:function(r){return r.refund;},render:function(r){return money2(r.refund);}},
      {t:'Top Reason',render:function(r){return cleanReason(r.topReason);}}
    ],sRows,{per:25});
    var isSku=(RETURNS_TAB==='sku');
    var tools='<div class="tabletools"><div class="tt-search"><span class="tt-ic">🔍</span>'+
      '<input class="tt-q" id="tt-returns-q" placeholder="'+(isSku?'Search SKU…':'Search order ID, SKU, reason…')+'" value="'+esc(f.q)+'" autocomplete="off"></div>'+
      '<select class="tt-select" id="tt-returns-mkt" title="Marketplace"><option value="">All marketplaces</option>'+
        channels.map(function(k){return '<option'+(k===selMkt?' selected':'')+'>'+esc(k)+'</option>';}).join('')+'</select>'+
      '<span class="tt-spacer"></span><span class="tt-count">'+n(isSku?sRows.length:rows.length)+' '+(isSku?'SKUs':'returns')+'</span>'+
      '<button type="button" class="tt-clear" id="tt-returns-clear">Clear</button></div>';
    var selLabel=selMkt?esc(selMkt):'All marketplaces';
    return sect('↩️ Returns','Returns for qualifying combo SKUs. Amazon: SKU/qty/reason direct. eBay: one row per return_id (real qty/reason/refund). Shopify: refund events bridged via order_id — qty from the order line, refund = refund_amount (no reason field at source). Showing: '+selLabel+'.')+
      '<div class="kpi-grid">'+cards+'</div>'+
      '<div class="panel"><h3>Returns by Channel</h3>'+miniBars(barRows,function(){return 'var(--red)';})+'</div>'+
      '<div class="panel"><div class="phead"><div><h3>'+(isSku?'🏷️ Returns by SKU':'📄 Return Records')+(selMkt?' <span class="muted">— '+esc(selMkt)+'</span>':'')+'</h3></div>'+tablist('returns',RETURNS_TAB,[['platform','Platform-wise'],['sku','SKU-wise']])+'</div>'+tools+(isSku?skuTable:t)+'</div>';
  };

  VIEWS.suppliers=function(){
    var c=CI, PO=CI.po, POMAP={};
    D.purchaseOrders.forEach(function(r){ POMAP[r[PO.po]]=r; });
    // active components -> active POs (respecting the date filter)
    var poComp={}; ACT.components.forEach(function(r){ var p=r[c.comp.po]; if(p) poComp[p]=(poComp[p]||0)+1; });
    var activePOs=Object.keys(poComp);
    // supplier summary (enriched from the PO detail)
    var sup={};
    ACT.components.forEach(function(r){var k=r[c.comp.sup]||'—'; var a=sup[k]||(sup[k]={sup:k,comps:0,po:{},cont:{}}); a.comps++; if(r[c.comp.po])a.po[r[c.comp.po]]=1; if(r[c.comp.cont])a.cont[r[c.comp.cont]]=1;});
    var supRows=Object.keys(sup).map(function(k){var a=sup[k], pos=Object.keys(a.po), cbm=0, arrived=0, latest='', code='';
      pos.forEach(function(p){var po=POMAP[p]; if(po){ cbm+=(po[PO.cbm]||0); if(po[PO.arrived]===1)arrived++; if(po[PO.order_date]>latest)latest=po[PO.order_date]; if(!code)code=po[PO.code]; }});
      return {sup:k,code:code,comps:a.comps,pos:pos.length,conts:Object.keys(a.cont).length,cbm:cbm,arrived:arrived,latest:latest};});
    // PO & container detail
    var poRows=activePOs.map(function(p){var po=POMAP[p]||[]; return {po:p,supplier:po[PO.supplier]||'—',code:po[PO.code]||'',order_date:po[PO.order_date]||'',container:po[PO.container]||'',cbm:po[PO.cbm],comps:poComp[p],confirmed:po[PO.confirmed]||'',finished:po[PO.finished]||'',expected:po[PO.expected]||'',arrived:po[PO.arrived]||0};});
    var totCbm=supRows.reduce(function(a,r){return a+r.cbm;},0), totArr=poRows.filter(function(r){return r.arrived===1;}).length;
    var cards=kpi('Suppliers',n(supRows.length),'','blue','','🏭')
      +kpi('Purchase Orders',n(activePOs.length),n(totArr)+' arrived','green','','📄')
      +kpi('Containers',n((function(){var s={};poRows.forEach(function(r){if(r.container)s[r.container]=1;});return Object.keys(s).length;})()),'','accent','','🚢')
      +kpi('Components',n(ACT.components.length),'','orange','','📦')
      +kpi('Total CBM',totCbm.toFixed(1)+' m³','ordered volume','blue','','📦');
    function arrChip(a){return a===1?chip('Arrived','green'):chip('In Transit','orange');}
    var f=gf('suppliers'), q=f.q.trim().toUpperCase(), isPO=(SUPPLIERS_TAB==='po');
    // supplier-wise table
    var sRows=q?supRows.filter(function(r){return (r.sup+' '+r.code).toUpperCase().indexOf(q)>=0;}):supRows;
    var supTable=tableP('sup',[
      {t:'Supplier',render:function(r){return '<b>'+esc(r.sup)+'</b>';}},
      {t:'Code',render:function(r){return r.code?chip(r.code,'gray'):'—';}},
      {t:'Components',num:true,sort:function(r){return r.comps;},render:function(r){return n(r.comps);}},
      {t:'POs',num:true,sort:function(r){return r.pos;},render:function(r){return n(r.pos);}},
      {t:'Containers',num:true,sort:function(r){return r.conts;},render:function(r){return n(r.conts);}},
      {t:'Total CBM (m³)',num:true,sort:function(r){return r.cbm;},render:function(r){return r.cbm.toFixed(2);}},
      {t:'Arrived POs',num:true,sort:function(r){return r.arrived;},render:function(r){return n(r.arrived);}},
      {t:'Latest Order',sort:function(r){return sDate(r.latest);},render:function(r){return r.latest||'—';}}
    ],sRows,{per:25});
    // PO & container-wise table
    var pRows=q?poRows.filter(function(r){return (r.po+' '+r.supplier+' '+r.code+' '+r.container).toUpperCase().indexOf(q)>=0;}):poRows;
    var poTable=tableP('supo',[
      {t:'PO',render:function(r){return '<b>'+esc(r.po)+'</b>';}},
      {t:'Supplier',render:function(r){return esc(r.supplier);}},
      {t:'Code',render:function(r){return r.code?chip(r.code,'gray'):'—';}},
      {t:'Order Date',sort:function(r){return sDate(r.order_date);},render:function(r){return r.order_date||'—';}},
      {t:'Container',render:function(r){return r.container?esc(r.container):chip('unassigned','gray');}},
      {t:'CBM (m³)',num:true,sort:function(r){return r.cbm==null?-1:r.cbm;},render:function(r){return r.cbm==null?'—':r.cbm.toFixed(2);}},
      {t:'Components',num:true,sort:function(r){return r.comps;},render:function(r){return n(r.comps);}},
      {t:'Confirmed',sort:function(r){return sDate(r.confirmed);},render:function(r){return r.confirmed||'—';}},
      {t:'Finished',sort:function(r){return sDate(r.finished);},render:function(r){return r.finished||'—';}},
      {t:'Expected Completion',sort:function(r){return sDate(r.expected);},render:function(r){return r.expected||'—';}},
      {t:'Arrived',sort:function(r){return r.arrived;},render:function(r){return arrChip(r.arrived);}}
    ],pRows,{per:25});
    var tools='<div class="tabletools"><div class="tt-search"><span class="tt-ic">🔍</span>'+
      '<input class="tt-q" id="tt-suppliers-q" placeholder="'+(isPO?'Search PO, supplier, container…':'Search supplier or code…')+'" value="'+esc(f.q)+'" autocomplete="off"></div>'+
      '<span class="tt-spacer"></span><span class="tt-count">'+n(isPO?pRows.length:sRows.length)+' '+(isPO?'POs':'suppliers')+'</span>'+
      '<button type="button" class="tt-clear" id="tt-suppliers-clear">Clear</button></div>';
    return sect('🚢 Supplier & Container','Suppliers, purchase orders and containers for the new components in range. Warehouse receive date does not exist — arrival = supplier.orders.status_arrived.')+
      '<div class="kpi-grid">'+cards+'</div>'+
      '<div class="panel"><div class="phead"><div><h3>'+(isPO?'📄 Purchase Orders & Containers':'🏭 Suppliers')+'</h3></div>'+tablist('suppliers',SUPPLIERS_TAB,[['supplier','Supplier-wise'],['po','PO & Container']])+'</div>'+tools+(isPO?poTable:supTable)+'</div>';
  };

  VIEWS.explorer=function(){
    return sect('🔍 SKU Explorer','Search across components, combos and orders in the selected period.')+
      '<div class="searchbig"><input id="expSearch" placeholder="e.g. LSCY290BM, WSNWBS…"><button class="btn" id="expBtn">Search</button></div><div id="expResult"></div>';
  };

  function sect(title,sub){ return '<h2 class="sectiontitle">'+title+'</h2><p class="sectionsub">'+esc(sub)+'</p>'; }

  function runExplorer(q){
    q=(q||'').trim(); var box=document.getElementById('expResult'); if(!box)return; if(!q){box.innerHTML='';return;}
    var Q=q.toUpperCase(), c=CI;
    var comps=ACT.components.filter(function(r){return (r[c.comp.sku]+' '+r[c.comp.desc]+' '+r[c.comp.sup]).toUpperCase().indexOf(Q)>=0;});
    var combos=ACT.combos.filter(function(r){return r[c.combo.sku].toUpperCase().indexOf(Q)>=0;});
    var out='';
    if(comps.length)out+='<div class="panel"><h3>📦 Components ('+comps.length+')</h3>'+tableP('exC',[{t:'SKU',render:function(r){return '<b>'+esc(r[c.comp.sku])+'</b>';}},{t:'Supplier',render:function(r){return esc(r[c.comp.sup]);}},{t:'PO',render:function(r){return esc(r[c.comp.po]);}},{t:'Created',render:function(r){return esc(r[c.comp.created]);}}],comps,{per:25})+'</div>';
    if(combos.length)out+='<div class="panel"><h3>🧩 Combos ('+combos.length+')</h3>'+tableP('exK',[{t:'Combo SKU',render:function(r){return '<b>'+esc(r[c.combo.sku])+'</b>';}},{t:'First Listed',render:function(r){return r[c.combo.first]||'—';}},{t:'Orders',num:true,render:function(r){var co=ACT.comboOrders[r[c.combo.sku]];return n(co?Object.keys(co.ord).length:0);}},{t:'Sales',num:true,render:function(r){var co=ACT.comboOrders[r[c.combo.sku]];return money(co?co.sales:0);}}],combos,{per:25})+'</div>';
    box.innerHTML=out||'<div class="panel"><p class="sectionsub">No match for “'+esc(q)+'” in range.</p></div>';
    wireTable('exC',null,function(){runExplorer(q);}); wireTable('exK',null,function(){runExplorer(q);});
  }

  /* ============================ ROUTER + INIT ============================ */
  var current=null;
  function render(view){
    var sameView=(view===current); current=view;
    var y=window.scrollY||window.pageYOffset||0;   // keep scroll on same-view re-renders (filter/search/sort/paging)
    document.querySelectorAll('#sidenav a').forEach(function(a){a.classList.toggle('active',a.getAttribute('data-view')===view);});
    content.innerHTML=(VIEWS[view]||VIEWS.dashboard)();
    /* [data-view] clicks, tables, toolbars & filters are handled by event delegation (wireDelegation) */
    if(view==='explorer'){var b=document.getElementById('expBtn'),i=document.getElementById('expSearch');b.onclick=function(){runExplorer(i.value);};i.addEventListener('keydown',function(e){if(e.key==='Enter')runExplorer(i.value);});}
    if(REFOCUS&&REFOCUS.view===view){var q=document.getElementById('tt-'+view+'-q');if(q){q.focus();try{q.setSelectionRange(REFOCUS.pos,REFOCUS.pos);}catch(e){}}REFOCUS=null;}
    else if(sameView){window.scrollTo(0,y);}   // preserve position (marketplace filter, sort, pagination)
    else{window.scrollTo(0,0);}                 // scroll to top only on real page navigation
    try{localStorage.setItem('scwts_view',view);}catch(e){}   // remember page across refresh (fallback to hash)
  }
  // navigate via the URL hash so the current page survives a refresh (and back/forward works)
  function hashView(){ var v=decodeURIComponent((location.hash||'').replace(/^#/,'')); return VIEWS[v]?v:'dashboard'; }
  // Navigate: render once, then update the URL hash silently via replaceState (does NOT fire hashchange,
  // so there is no double-render). replaceState keeps the hash in the URL so a refresh restores the view.
  function go(view){
    if(!VIEWS[view])view='dashboard';
    PAGE={}; render(view);
    // keep the URL hash in sync (so a refresh restores this view) without firing hashchange -> no double render
    try{ history.replaceState(null,'','#'+view); }
    catch(e){ if(('#'+view)!==location.hash){ try{location.hash=view;}catch(_){} } }
  }
  function reloadAll(){ compute(); PAGE={}; render(current); }
  function rerender(){ if(current==='explorer'){ var i=document.getElementById('expSearch'); runExplorer(i?i.value:''); } else render(current); }
  // Event delegation on the persistent #content container — immune to re-render/timing staleness.
  function wireDelegation(){
    content.addEventListener('input',function(e){
      var t=e.target; if(t&&t.classList&&t.classList.contains('tt-q')){ var v=t.id.slice(3,-2); gf(v).q=t.value; PAGE={}; REFOCUS={view:v,pos:t.selectionStart}; render(v); }
    });
    content.addEventListener('change',function(e){
      var t=e.target, id=t.id||'';
      if(t.classList&&t.classList.contains('perpage')){ var pid=t.getAttribute('data-id'); PER[pid]=+t.value; PAGE[pid]=0; rerender(); return; }
      if(id==='tt-traffic-mkt'){ TRAFFIC_MKT=t.value; PAGE={}; render('traffic'); }
      else if(id==='tt-traffic-src'){ TRAFFIC_SRC=t.value; PAGE={}; render('traffic'); }
      else if(id==='tt-returns-mkt'){ RETURNS_MKT=t.value; PAGE={}; render('returns'); }
      else if(id==='tt-sales-mkt'){ SALES_MKT=t.value; PAGE={}; render('sales'); }
    });
    content.addEventListener('click',function(e){
      var t=e.target, el; if(!t||!t.closest) return;
      if(el=t.closest('.tab')){ var grp=el.getAttribute('data-tab-group'), tb=el.getAttribute('data-tab');
        if(grp==='sales')SALES_TAB=tb; else if(grp==='returns')RETURNS_TAB=tb; else if(grp==='suppliers')SUPPLIERS_TAB=tb; PAGE={}; render(grp); return; }
      if(el=t.closest('.tt-clear')){ var v=el.id.slice(3,-6); FILTERS[v]={q:''}; if(v==='traffic'){TRAFFIC_MKT='';TRAFFIC_SRC='';} if(v==='returns')RETURNS_MKT=''; if(v==='sales')SALES_MKT=''; PAGE={}; render(v); return; }
      if(el=t.closest('.mktcard')){ MKT_SEL=el.getAttribute('data-mkt'); PAGE={}; render('marketplace'); return; }
      if(el=t.closest('button.pg')){ var id=el.getAttribute('data-id'); PAGE[id]=(PAGE[id]||0)+(+el.getAttribute('data-d')); if(PAGE[id]<0)PAGE[id]=0; rerender(); return; }
      if(el=t.closest('th.sortable')){ var sid=el.getAttribute('data-sort-id'),ci=+el.getAttribute('data-ci'),cur=SORT[sid]; if(cur&&cur.ci===ci)cur.dir=-cur.dir; else SORT[sid]={ci:ci,dir:-1}; PAGE[sid]=0; rerender(); return; }
      if(el=t.closest('[data-view]')){ go(el.getAttribute('data-view')); return; }
      if(el=t.closest('tr.clickable')){ var w=el.closest('[data-tid]'); if(!w)return; var tid=w.getAttribute('data-tid'); var row=(RROWS[tid]||[])[+el.getAttribute('data-ri')]; if(!row)return; if(tid==='combos'||tid==='exK')openCombo(row); else openComponent(row); return; }
    });
  }

  function init(){
    var from=document.getElementById('fromDate'), to=document.getElementById('toDate');
    from.value=FROM; to.value=TO; from.min=D.meta.periodStart; to.max=D.meta.periodEnd; from.max=D.meta.periodEnd; to.min=D.meta.periodStart;
    document.getElementById('refreshInfo').textContent=D.meta.capturedAt;
    from.addEventListener('change',function(){ FROM=from.value||D.meta.periodStart; if(FROM>TO){TO=FROM;to.value=TO;} reloadAll(); });
    to.addEventListener('change',function(){ TO=to.value||D.meta.periodEnd; if(TO<FROM){FROM=TO;from.value=FROM;} reloadAll(); });
    var cb=document.getElementById('collapseBtn'); if(cb)cb.onclick=function(){document.body.classList.toggle('nav-collapsed');};
    document.querySelectorAll('#sidenav a').forEach(function(a){a.addEventListener('click',function(e){e.preventDefault();go(a.getAttribute('data-view'));});});
    wireDelegation();
    document.getElementById('themeBtn').onclick=function(){var el=document.documentElement;el.setAttribute('data-theme',el.getAttribute('data-theme')==='dark'?'light':'dark');};
    document.getElementById('exportBtn').onclick=exportCsv;
    var initV=hashView();
    if(!location.hash||location.hash==='#'){ try{var ls=localStorage.getItem('scwts_view'); if(ls&&VIEWS[ls]) initV=ls;}catch(e){} }
    compute(); go(initV);   // restore last view (URL hash first, else localStorage) and sync the URL
  }
  function exportCsv(){
    var c=CI, head=['Component SKU','Description','Supplier','PO','Container','Created','Combos','Markets','Status'];
    var rows=ACT.components.map(function(r){var sku=r[c.comp.sku];var cb=ACT.compCombos[sku]?Object.keys(ACT.compCombos[sku]).length:0;var mk=ACT.compMarkets[sku]?Object.keys(ACT.compMarkets[sku]).length:0;return [sku,r[c.comp.desc],r[c.comp.sup],r[c.comp.po],r[c.comp.cont],r[c.comp.created],cb,mk,(cb&&mk?'Selling':mk?'Listed':cb?'Has Combo':'No Combo')];});
    var csv=[head].concat(rows).map(function(r){return r.map(function(x){return '"'+String(x==null?'':x).replace(/"/g,'""')+'"';}).join(',');}).join('\n');
    var a=document.createElement('a');a.href='data:text/csv;charset=utf-8,'+encodeURIComponent(csv);a.download='component_journey_'+FROM+'_'+TO+'.csv';a.click();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
