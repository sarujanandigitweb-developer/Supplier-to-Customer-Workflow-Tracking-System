/* Supplier-to-Customer Workflow Tracking — app logic. Consumes the live PostgreSQL snapshot in data.js. */
(function(){
  "use strict";
  var D = window.DASHBOARD_DATA;
  var content = document.getElementById('content');

  function n(x){ return (x==null?0:Math.round(x)).toLocaleString('en-GB'); }
  function money(x){ return '£'+(x||0).toLocaleString('en-GB',{maximumFractionDigits:0}); }
  function money2(x){ return '£'+(x||0).toLocaleString('en-GB',{minimumFractionDigits:2,maximumFractionDigits:2}); }
  function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
  function pct(a,b){ return b? ((a/b)*100).toFixed(1)+'%' : '—'; }

  var TONE_ICON={green:'📦',blue:'📊',orange:'⚠️',red:'↩️',accent:'🏷️',gray:'▫️'};
  function kpi(label,val,sub,tone,view,icon,note){
    icon=icon||TONE_ICON[tone]||'•';
    var noteHtml=note?'<span class="kpi-note">'+esc(note)+'</span>':'';
    return '<div class="kpi k-'+tone+'"'+(view?' data-view="'+view+'"':'')+'>'+
      '<div class="kpi-top"><div class="kpi-ic">'+icon+'</div>'+
      '<div class="kpi-label">'+esc(label)+noteHtml+'</div></div>'+
      '<div class="val">'+val+'</div>'+(sub?'<div class="sub">'+esc(sub)+'</div>':'')+'</div>';
  }
  var CH_COLOR={amazon:'#ff9900',ebay:'#e53238',shopify:'#96bf48','B&Q':'#f28f1c'};

  /* ---- SVG line chart ---- */
  function lineChart(series,opts){
    opts=opts||{}; var W=720,H=220,pad=38;
    var max=Math.max.apply(null,series.map(function(p){return p.v;}))||1;
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
    var max=Math.max.apply(null,rows.map(function(r){return r.v;}))||1;
    return '<div class="mbar">'+rows.map(function(r){var c=colorFn?colorFn(r):'var(--accent)';
      return '<div class="row"><div>'+esc(r.l)+'</div><div class="track"><div class="fill" style="width:'+(r.v/max*100).toFixed(1)+'%;background:'+c+'"></div></div><div class="num">'+n(r.v)+'</div></div>';}).join('')+'</div>';
  }

  /* ---- sort helpers (date + count/number columns) ---- */
  function sDate(v){ v=(v==null?'':String(v)); return /^\d{4}-\d{2}-\d{2}/.test(v)? v : null; } // ISO strings compare correctly
  function sNum(v){ v=+v; return isNaN(v)? null : v; }

  /* ---- paginated + sortable table ---- */
  var PAGE={}, PER={}, PER_OPTS=[10,25,50,100], SORT={}, RENDER_ROWS={};
  function tableP(id, cols, rows, opts){
    opts=opts||{};
    // apply sort on a copy so the caller's source array is never mutated
    var data=rows.slice();
    var srt=SORT[id];
    if(srt && cols[srt.ci] && cols[srt.ci].sort){
      var acc=cols[srt.ci].sort, dir=srt.dir;
      data.sort(function(a,b){
        var va=acc(a), vb=acc(b);
        if(va==null&&vb==null) return 0;
        if(va==null) return 1;            // nulls / blanks always last
        if(vb==null) return -1;
        return va<vb ? -dir : va>vb ? dir : 0;
      });
    }
    RENDER_ROWS[id]=data;                  // exact order the data-ri indices point into
    var per = (PER[id]!=null ? PER[id] : (opts.per||25));
    if(PAGE[id]==null) PAGE[id]=0;
    var pages=Math.max(1,Math.ceil(data.length/per)); if(PAGE[id]>=pages) PAGE[id]=0;
    var start=PAGE[id]*per, slice=data.slice(start,start+per);
    var thead='<tr>'+cols.map(function(c,ci){
      var sortable=!!c.sort, active=srt&&srt.ci===ci;
      var arrow = active ? '<span class="sarrow">'+(srt.dir>0?'▲':'▼')+'</span>'
                : sortable ? '<span class="sarrow dim">↕</span>' : '';
      var cls=(c.num?'num ':'')+(sortable?'sortable':'')+(active?' sorted':'');
      return '<th class="'+cls.replace(/\s+/g,' ').trim()+'"'+(sortable?' data-sort-id="'+id+'" data-ci="'+ci+'"':'')+'>'+esc(c.t)+arrow+'</th>';
    }).join('')+'</tr>';
    var body=slice.map(function(r,i){
      var tds=cols.map(function(c){var v=c.render?c.render(r):r[c.k]; return '<td class="'+(c.num?'num':'')+'">'+(v==null?'':v)+'</td>';}).join('');
      return '<tr class="'+(opts.onRow?'clickable':'')+'" data-ri="'+(start+i)+'">'+tds+'</tr>';
    }).join('');
    // rows-per-page selector — shown for real tables (hidden on small previews)
    var showPer = opts.perPage!==false && data.length>PER_OPTS[0];
    var perSel = showPer ? '<label class="perpage-wrap">Rows per page'+
      ' <select class="perpage" data-id="'+id+'" title="Rows per page">'+
      PER_OPTS.map(function(v){return '<option value="'+v+'"'+(v==per?' selected':'')+'>'+v+'</option>';}).join('')+
      '</select></label>' : '';
    var pager = pages>1 ? '<span class="pagebtns"><button type="button" class="btn pg" data-id="'+id+'" data-d="-1">‹ Prev</button>'+
      '<span>Page '+(PAGE[id]+1)+' / '+pages+'</span>'+
      '<button type="button" class="btn pg" data-id="'+id+'" data-d="1">Next ›</button></span>' : '';
    var info='Showing '+(data.length?start+1:0)+'–'+Math.min(start+per,data.length)+' of '+n(data.length);
    var ctrl='<div class="pageinfo"><span class="pginfo-left">'+info+perSel+'</span>'+pager+'</div>';
    return '<div class="tablewrap" data-tid="'+id+'"><table><thead>'+thead+'</thead><tbody>'+body+'</tbody></table></div>'+ctrl;
  }
  function wirePager(rerender){
    content.querySelectorAll('button.pg').forEach(function(b){
      b.addEventListener('click',function(){ var id=b.getAttribute('data-id'); PAGE[id]=(PAGE[id]||0)+(+b.getAttribute('data-d')); if(PAGE[id]<0)PAGE[id]=0; rerender(); });
    });
    content.querySelectorAll('select.perpage').forEach(function(s){
      s.addEventListener('change',function(){ var id=s.getAttribute('data-id'); PER[id]=+s.value; PAGE[id]=0; rerender(); });
    });
    content.querySelectorAll('th.sortable').forEach(function(th){
      th.addEventListener('click',function(){
        var id=th.getAttribute('data-sort-id'), ci=+th.getAttribute('data-ci'), cur=SORT[id];
        if(cur && cur.ci===ci){ cur.dir=-cur.dir; } else { SORT[id]={ci:ci, dir:-1}; } // first click = descending
        PAGE[id]=0; rerender();
      });
    });
  }
  function wireRows(id,onRow){
    var data=RENDER_ROWS[id]||[], scope=content.querySelector('[data-tid="'+id+'"]'); if(!scope) return;
    scope.querySelectorAll('tbody tr.clickable').forEach(function(tr){ tr.addEventListener('click',function(){onRow(data[+tr.getAttribute('data-ri')]);}); });
  }

  function chip(txt,tone){ return '<span class="chip '+tone+'">'+esc(txt)+'</span>'; }
  function listingChip(mkt){ return mkt>0? chip('Listed ('+mkt+')','green') : chip('Not Listed','gray'); }
  function statusChip(s){
    var m={'Selling':'green','Listed':'blue','Has Combo':'orange','No Combo':'gray','Ended':'orange','Not Listed':'red'};
    return chip(s, m[s]||'gray');
  }

  /* ---- returns lookup for combos ---- */
  var RET_MAP={}; (D.returns.amazonBySku||[]).forEach(function(r){ RET_MAP[r.sku]=(RET_MAP[r.sku]||0)+r.qty; });

  /* =================== VIEWS =================== */
  var VIEWS={};

  function stageIcon(name){
    var s=String(name).toLowerCase();
    if(s.indexOf('supplier')>=0) return '🏭';
    if(s==='po'||s.indexOf('purchase')>=0) return '📄';
    if(s.indexOf('container')>=0) return '🚢';
    if(s.indexOf('component')>=0) return '📦';
    if(s.indexOf('combo')>=0) return '🧩';
    if(s.indexOf('list')>=0) return '✅';
    if(s.indexOf('return')>=0) return '↩️';
    if(s.indexOf('order')>=0) return '🛒';
    return '•';
  }
  function funnelH(stages){
    var nodes=stages.map(function(f,i){
      var st=f.value>0?'ok':'nodata';
      var arrow=i?'<div class="farrow">→</div>':'';
      return arrow+'<div class="fnode '+st+'" data-view="'+f.view+'"><div class="fcircle">'+stageIcon(f.stage)+'</div><div class="fname">'+esc(f.stage)+'</div><div class="fval">'+n(f.value)+'</div></div>';
    }).join('');
    var legend='<div class="flegend"><span><i class="green"></i>Completed</span><span><i class="blue"></i>In Progress</span><span><i class="orange"></i>Pending</span><span><i class="gray"></i>No Data</span></div>';
    return '<div class="funnel-h">'+nodes+'</div>'+legend;
  }
  function phead(title, sub, btnLabel, btnView){
    var btn=btnLabel?'<button type="button" class="viewall" data-view="'+btnView+'">'+esc(btnLabel)+'</button>':'';
    var s=sub?'<div class="sub">'+esc(sub)+'</div>':'';
    return '<div class="phead"><div><h3>'+title+'</h3>'+s+'</div>'+btn+'</div>';
  }

  VIEWS.dashboard=function(){
    var k=D.kpi;
    var cards=kpi('New Components',n(k.newComponentsSinceMarch),n(k.componentRowsSinceMarch)+' order lines','green','journey','📦','(Since Mar 01, 2026)')
      +kpi('Combo SKUs Created',n(k.combosCreatedSinceMarch),'From new components','blue','combos','🧩','(Since Mar 01, 2026)')
      +kpi('Listed Combo SKUs',n(k.listedCombosTotal),'Total listed across channels','green','marketplace','✅')
      +kpi('Non-Listed Combo SKUs',n(k.nonListedCombosTotal),'Not yet listed','orange','marketplace','⛔')
      +kpi('Orders',n(k.orders),'Completed orders','accent','sales','🛒')
      +kpi('Sales',money(k.sales),'Revenue (AOV '+money2(k.aov)+')','red','sales','💷');
    var salesSeries=D.salesTrend.map(function(p){return {l:p.month,v:p.sales};});
    var mkt=D.marketplaceDist.map(function(m){return {l:m.channel,v:m.listings};});
    var latestComp=tableP('dashComp',[{t:'SKU',render:function(r){return '<b>'+esc(r[0])+'</b>';}},{t:'Supplier',render:function(r){return esc(r[2]);}},{t:'Created',render:function(r){return esc(r[5]);}},{t:'Combos',num:true,render:function(r){return n(r[6]);}},{t:'Status',render:function(r){return statusChip(r[9]);}}],D.componentJourney.slice(0,8),{per:8});
    var latestCombo=tableP('dashCombo',[{t:'Combo SKU',render:function(r){return '<b>'+esc(r.sku)+'</b>';}},{t:'Created',render:function(r){return r.created;}},{t:'Sales',num:true,render:function(r){return money(r.sales);}}],D.topCombos.slice(0,8),{per:8});
    return '<div class="kpi-grid">'+cards+'</div>'+
      '<div class="panel">'+phead('🚦 Journey Funnel <span class="muted">— click a stage to drill down</span>')+funnelH(D.funnel)+'</div>'+
      '<div class="grid-2">'+
        '<div class="panel"><div class="phead"><div><h3>📈 Sales Trend <span class="muted">— '+esc(D.meta.periodLabel)+'</span></h3></div><span class="ctrl">📅 Grouped by Month</span></div>'+lineChart(salesSeries,{money:true})+'</div>'+
        '<div class="panel">'+phead('🌍 Marketplace Distribution')+miniBars(mkt,function(r){return CH_COLOR[r.l]||'var(--accent)';})+'</div>'+
      '</div>'+
      '<div class="grid-2">'+
        '<div class="panel">'+phead('📦 Latest New Components','',' View all ','journey')+latestComp+'</div>'+
        '<div class="panel">'+phead('🧩 Top Combo SKUs','',' View all ','combos')+latestCombo+'</div>'+
      '</div>';
  };

  VIEWS.journey=function(){
    var rows=filterJourney(D.componentJourney);
    var t=tableP('journey',[
      {t:'Component SKU',render:function(r){return '<b>'+esc(r[0])+'</b>';}},
      {t:'Description',render:function(r){return esc(r[1]);}},
      {t:'Supplier',render:function(r){return esc(r[2]);}},
      {t:'PO',render:function(r){return esc(r[3]);}},
      {t:'Container',render:function(r){return r[4]==='—'?chip('—','gray'):esc(r[4]);}},
      {t:'Created',sort:function(r){return sDate(r[5]);},render:function(r){return esc(r[5]);}},
      {t:'Combos',num:true,sort:function(r){return sNum(r[6]);},render:function(r){return n(r[6]);}},
      {t:'Markets',num:true,sort:function(r){return sNum(r[7]);},render:function(r){return listingChip(r[7]);}},
      {t:'Listing',render:function(r){return statusChip(r[8]);}},
      {t:'Status',render:function(r){return statusChip(r[9]);}}
    ],rows,{per:25,onRow:true});
    setTimeout(function(){wireRows('journey',openComponent); wirePager(function(){render('journey');});},0);
    return '<h2 class="sectiontitle">📦 Component Journey</h2><p class="sectionsub">All '+n(rows.length)+' new components since March 01, 2026 — supplier → PO → container → market. Click a row to trace it.</p><div class="panel">'+t+'</div>';
  };

  VIEWS.combos=function(){
    var c=D.comboStats;
    var cards=kpi('Total Components',n(c.totalComponents),'supplier.order_items','blue')
      +kpi('Combos Created (since Mar)',n(c.marketplaceCombosCreated),'listing_data','accent','')
      +kpi('Supplier-Defined Combos',n(c.supplierDefinedCombos),c.comboLinks+' links','gray')
      +kpi('Avg Components / Combo',c.avgComponentsPerComboSample,'sample','blue');
    var rows=D.topCombos;
    var t=tableP('combos',[
      {t:'Combo SKU',render:function(r){return '<b>'+esc(r.sku)+'</b>';}},
      {t:'Parent Components',render:function(r){return esc(r.sku.split('+').join(' + '));}},
      {t:'Created',sort:function(r){return sDate(r.created);},render:function(r){return r.created;}},
      {t:'Markets',num:true,sort:function(r){return sNum(r.marketplaces);},render:function(r){return n(r.marketplaces);}},
      {t:'Orders',num:true,sort:function(r){return sNum(r.orders);},render:function(r){return n(r.orders);}},
      {t:'Sales',num:true,sort:function(r){return sNum(r.sales);},render:function(r){return money(r.sales);}},
      {t:'Returns',num:true,sort:function(r){return sNum(RET_MAP[r.sku]||0);},render:function(r){return RET_MAP[r.sku]?n(RET_MAP[r.sku]):'—';}}
    ],rows,{per:25,onRow:true});
    setTimeout(function(){wireRows('combos',openCombo); wirePager(function(){render('combos');});},0);
    return '<h2 class="sectiontitle">🧩 Combo Creation</h2><p class="sectionsub">'+n(c.marketplaceCombosCreated)+' combo SKUs created since March. Top by sales shown below (returns from amazon_returns where matched).</p><div class="kpi-grid">'+cards+'</div><div class="panel"><h3>Top Combo SKUs Created (period)</h3>'+t+'</div>';
  };

  VIEWS.marketplace=function(){
    var CH_ICON={amazon:'🛒',ebay:'🏷️',shopify:'🛍️','B&Q':'🔧'};
    var cards=D.marketplaceDist.map(function(m){
      return '<div class="kpi k-blue">'+
        '<div class="kpi-top"><div class="kpi-ic">'+(CH_ICON[m.channel]||'🌍')+'</div>'+
        '<div class="kpi-label">'+esc(m.channel)+'</div></div>'+
        '<div class="val">'+n(m.listings)+'</div>'+
        '<div class="sub">'+n(m.combos)+' combo SKUs</div></div>';
    }).join('');
    var rows=filterMarket(D.marketplaceSample);
    var t=tableP('mkt',[
      {t:'SKU',render:function(r){return '<b>'+esc(r[0])+'</b>';}},
      {t:'Marketplace',render:function(r){return esc(r[1])+' · '+esc(r[2]);}},
      {t:'Status',render:function(r){return statusChip(r[3]);}},
      {t:'Listing Date',sort:function(r){return sDate(r[4]);},render:function(r){return esc(r[4]);}},
      {t:'Days Live',num:true,sort:function(r){return sNum(r[5]);},render:function(r){return n(r[5]);}},
      {t:'Wrong SKU',render:function(r){return r[6]?chip('Yes','red'):chip('No','green');}},
      {t:'Ended',render:function(r){return r[7]?chip('Yes','orange'):chip('No','gray');}}
    ],rows,{per:25});
    setTimeout(function(){wirePager(function(){render('marketplace');});},0);
    return '<h2 class="sectiontitle">🌍 Marketplace Status</h2><p class="sectionsub">Listings created since March 01, 2026 (public.listing_data). Sample of newest '+rows.length+' shown.</p><div class="kpi-grid">'+cards+'</div><div class="panel"><h3>Recently Listed SKUs</h3>'+t+'</div>';
  };

  VIEWS.sales=function(){
    var k=D.kpi;
    var cards=kpi('Orders',n(k.orders),'Completed','accent')
      +kpi('Revenue',money(k.sales),'','green')
      +kpi('Units',n(k.units),'','blue')
      +kpi('Avg Order Value',money2(k.aov),'','blue')
      +kpi('Returns',n(k.returnsLines),pct(k.returnsLines,k.orders)+' of orders','red');
    var salesSeries=D.salesTrend.map(function(p){return {l:p.month,v:p.sales};});
    var orderSeries=D.salesTrend.map(function(p){return {l:p.month,v:p.orders};});
    var top=tableP('topsku',[
      {t:'SKU',render:function(r){return '<b>'+esc(r.sku)+'</b>';}},
      {t:'Type',render:function(r){return r.isCombo?chip('Combo','blue'):chip('Component','gray');}},
      {t:'Orders',num:true,sort:function(r){return sNum(r.orders);},render:function(r){return n(r.orders);}},
      {t:'Units',num:true,sort:function(r){return sNum(r.units);},render:function(r){return n(r.units);}},
      {t:'Sales',num:true,sort:function(r){return sNum(r.sales);},render:function(r){return money(r.sales);}}
    ],D.topSKUs,{per:25});
    setTimeout(function(){wirePager(function(){render('sales');});},0);
    return '<h2 class="sectiontitle">📈 Sales Performance</h2><p class="sectionsub">public.order_transaction · '+esc(D.meta.periodLabel)+' · Completed orders.</p><div class="kpi-grid">'+cards+'</div>'+
      '<div class="grid-2"><div class="panel"><h3>Sales Trend</h3>'+lineChart(salesSeries,{money:true})+'</div><div class="panel"><h3>Orders Trend</h3>'+lineChart(orderSeries,{})+'</div></div>'+
      '<div class="panel"><h3>🚦 Traffic <span class="muted">— traffic_data (organic) + ppc_performance (paid)</span></h3><div class="note">Impressions / Clicks / CTR require an aggregate over traffic_data (9.3M) + ppc_performance (27M). The DB pool closed during this pull, so these are not in the current snapshot. Re-run <code>gen_data.py</code> after querying to populate. <b>No placeholder values are shown.</b></div></div>'+
      '<div class="panel"><h3>🏆 Top Selling SKUs</h3>'+top+'</div>';
  };

  VIEWS.returns=function(){
    var r=D.returns, c=r.channel;
    var cards=kpi('Total Return Lines',n(r.linesTotal),'since Mar','red')
      +kpi('Amazon',n(c.amazon.lines),c.amazon.qty+' units','orange','')
      +kpi('eBay',n(c.ebay.lines),c.ebay.qty+' units','orange','')
      +kpi('Shopify',n(c.shopify.lines),'','gray');
    var byChannel=[{l:'eBay',v:c.ebay.lines},{l:'Amazon',v:c.amazon.lines},{l:'Shopify',v:c.shopify.lines}];
    var rows=r.amazonBySku;
    var t=tableP('ret',[
      {t:'SKU',render:function(r){return '<b>'+esc(r.sku)+'</b>';}},
      {t:'Marketplace',render:function(){return 'Amazon';}},
      {t:'Return Qty',num:true,sort:function(r){return sNum(r.qty);},render:function(r){return n(r.qty);}},
      {t:'Reason',render:function(r){return esc(r.reason.replace('CR-','').replace('AMZ-PG-',''));}}
    ],rows,{per:20});
    setTimeout(function(){wirePager(function(){render('returns');});},0);
    return '<h2 class="sectiontitle">↩️ Returns</h2><p class="sectionsub">Period returns across Amazon, eBay, Shopify. Per-SKU detail is Amazon-only (eBay/Shopify returns carry no SKU column).</p><div class="kpi-grid">'+cards+'</div>'+
      '<div class="panel"><h3>Returns by Channel (lines)</h3>'+miniBars(byChannel,function(){return 'var(--red)';})+'</div>'+
      '<div class="panel"><h3>Top Returned SKUs — Amazon</h3>'+t+'</div>';
  };

  VIEWS.suppliers=function(){
    var k=D.kpi;
    var cards=kpi('Suppliers',n(k.suppliers),'','blue')
      +kpi('Purchase Orders',n(k.purchaseOrders),k.posSinceMarch+' since Mar','green')
      +kpi('Containers',n(k.containers),k.finalContainers+' finalized','accent')
      +kpi('Components',n(k.componentsTotal),'','orange');
    var rows=filterPO(D.purchaseOrders);
    var t=tableP('po',[
      {t:'Supplier',render:function(r){return '<b>'+esc(r[0])+'</b>';}},
      {t:'PO',render:function(r){return esc(r[1]);}},
      {t:'Container',render:function(r){return r[2]?esc(r[2]):chip('unassigned','gray');}},
      {t:'Arrived',render:function(r){return r[3]==='Arrived'?chip('Arrived','green'):chip('In Transit','orange');}},
      {t:'Order Date',sort:function(r){return sDate(r[4]);},render:function(r){return esc(r[4]);}},
      {t:'Expected Completion',sort:function(r){return sDate(r[5]);},render:function(r){return r[5]?esc(r[5]):'—';}},
      {t:'Finished Date',sort:function(r){return sDate(r[6]);},render:function(r){return r[6]?esc(r[6]):'—';}}
    ],rows,{per:25});
    setTimeout(function(){wirePager(function(){render('suppliers');});},0);
    return '<h2 class="sectiontitle">🚢 Supplier &amp; Container</h2><p class="sectionsub">Purchase orders since March 01, 2026 ('+n(rows.length)+').</p>'+
      '<div class="note">ℹ️ <b>Warehouse Receive Date does not exist</b> in the database. Arrival is shown only via <code>supplier.orders.status_arrived</code>.</div>'+
      '<div class="kpi-grid">'+cards+'</div><div class="panel"><h3>Purchase Orders</h3>'+t+'</div>';
  };

  VIEWS.explorer=function(){
    return '<h2 class="sectiontitle">🔍 SKU Explorer</h2><p class="sectionsub">Search Component SKU · Combo SKU · Marketplace SKU · ASIN · Supplier · PO.</p><div class="searchbig"><input id="expSearch" placeholder="e.g. LSCY290BM, CAB072026, Cable Supplier…"><button class="btn" id="expBtn">Search</button></div><div id="expResult"></div>';
  };

  /* ---- filters ---- */
  function fv(id){var e=document.getElementById(id); return e?e.value:'';}
  function filterJourney(rows){
    var sup=fv('fSupplier'),cont=fv('fContainer'),q=fv('fSearch').trim().toUpperCase(),st=fv('fStatus');
    return rows.filter(function(r){
      if(sup && r[2]!==sup) return false;
      if(cont && r[4]!==cont) return false;
      if(st==='Listed' && r[7]<=0) return false;
      if(st==='Not Listed' && r[7]>0) return false;
      if(st==='Has Combo' && r[6]<=0) return false;
      if(st==='No Combo' && r[6]>0) return false;
      if(q && (r[0]+' '+r[1]+' '+r[3]).toUpperCase().indexOf(q)<0) return false;
      return true;
    });
  }
  function filterMarket(rows){var m=fv('fMarket'); return rows.filter(function(r){return !m||r[1]===m;});}
  function filterPO(rows){var sup=fv('fSupplier'),cont=fv('fContainer'); return rows.filter(function(r){if(sup&&r[0]!==sup)return false; if(cont&&r[2]!==cont)return false; return true;});}

  /* ---- drilldowns ---- */
  function modal(title,body){document.getElementById('modalRoot').innerHTML='<div class="modal-bg" id="mbg"><div class="modal"><div class="mhead"><h3>'+title+'</h3><button class="close-x" id="mx">×</button></div><div class="mbody">'+body+'</div></div></div>';document.getElementById('mx').onclick=closeModal;document.getElementById('mbg').onclick=function(e){if(e.target.id==='mbg')closeModal();};}
  function closeModal(){document.getElementById('modalRoot').innerHTML='';}
  function chain(nodes){return '<div class="chain">'+nodes.map(function(nd,i){return (i?'<span class="sep">→</span>':'')+'<div class="node"><b>'+esc(nd[0])+'</b>'+esc(nd[1])+'</div>';}).join('')+'</div>';}
  function openComponent(r){
    modal('📦 Component: '+esc(r[0]),
      chain([['Supplier',r[2]],['PO',r[3]],['Container',r[4]==='—'?'unassigned':r[4]],['Component',r[0]],['Combos',r[6]+''],['Markets',r[7]+' ch']])+
      '<p>'+esc(r[1]||'—')+'</p><div class="kpi-grid">'+kpi('Created',r[5],'','blue')+kpi('Combo Count',n(r[6]),'','accent')+kpi('Listing',r[8],'',(r[7]>0?'green':'red'))+kpi('Status',r[9],'','orange')+'</div>');
  }
  function openCombo(r){
    var parts=r.sku.split('+');
    modal('🧩 Combo: '+esc(r.sku),chain(parts.map(function(p){return ['Component',p];}))+'<div class="kpi-grid">'+kpi('Created',r.created,'','blue')+kpi('Markets',r.marketplaces,'','accent')+kpi('Orders',n(r.orders),'','green')+kpi('Sales',money(r.sales),'','blue')+kpi('Returns',RET_MAP[r.sku]?n(RET_MAP[r.sku]):'0','','red')+'</div><p class="sectionsub">Built from '+parts.length+' components.</p>');
  }

  /* ---- SKU explorer ---- */
  function runExplorer(q){
    q=(q||'').trim(); var box=document.getElementById('expResult'); if(!q){box.innerHTML='';return;}
    var Q=q.toUpperCase();
    var comps=D.componentJourney.filter(function(r){return (r[0]+' '+r[1]+' '+r[2]+' '+r[3]).toUpperCase().indexOf(Q)>=0;});
    var combos=D.topCombos.filter(function(r){return r.sku.toUpperCase().indexOf(Q)>=0;});
    var skus=D.topSKUs.filter(function(r){return r.sku.toUpperCase().indexOf(Q)>=0;});
    var ps=D.purchaseOrders.filter(function(r){return (r[0]+' '+r[1]+' '+(r[2]||'')).toUpperCase().indexOf(Q)>=0;});
    var out='';
    if(comps.length) out+='<div class="panel"><h3>📦 Components ('+comps.length+')</h3>'+tableP('exC',[{t:'SKU',render:function(r){return '<b>'+esc(r[0])+'</b>';}},{t:'Supplier',render:function(r){return esc(r[2]);}},{t:'PO',render:function(r){return esc(r[3]);}},{t:'Container',render:function(r){return esc(r[4]);}},{t:'Created',sort:function(r){return sDate(r[5]);},render:function(r){return esc(r[5]);}},{t:'Status',render:function(r){return statusChip(r[9]);}}],comps,{per:15,onRow:true})+'</div>';
    if(combos.length) out+='<div class="panel"><h3>🧩 Combos ('+combos.length+')</h3>'+tableP('exK',[{t:'Combo SKU',render:function(r){return '<b>'+esc(r.sku)+'</b>';}},{t:'Created',sort:function(r){return sDate(r.created);},render:function(r){return r.created;}},{t:'Orders',num:true,sort:function(r){return sNum(r.orders);},render:function(r){return n(r.orders);}},{t:'Sales',num:true,sort:function(r){return sNum(r.sales);},render:function(r){return money(r.sales);}}],combos,{per:15})+'</div>';
    if(skus.length) out+='<div class="panel"><h3>📈 Sales SKUs ('+skus.length+')</h3>'+tableP('exS',[{t:'SKU',render:function(r){return '<b>'+esc(r.sku)+'</b>';}},{t:'Orders',num:true,sort:function(r){return sNum(r.orders);},render:function(r){return n(r.orders);}},{t:'Units',num:true,sort:function(r){return sNum(r.units);},render:function(r){return n(r.units);}},{t:'Sales',num:true,sort:function(r){return sNum(r.sales);},render:function(r){return money(r.sales);}}],skus,{per:15})+'</div>';
    if(ps.length) out+='<div class="panel"><h3>🚢 Purchase Orders ('+ps.length+')</h3>'+tableP('exP',[{t:'Supplier',render:function(r){return esc(r[0]);}},{t:'PO',render:function(r){return '<b>'+esc(r[1])+'</b>';}},{t:'Container',render:function(r){return esc(r[2]||'—');}},{t:'Order Date',sort:function(r){return sDate(r[4]);},render:function(r){return esc(r[4]);}}],ps,{per:15})+'</div>';
    box.innerHTML=out||'<div class="panel"><p class="sectionsub">No match for “'+esc(q)+'” in the loaded snapshot.</p></div>';
    wirePager(function(){runExplorer(q);}); wireRows('exC',openComponent);
  }

  /* ---- router ---- */
  var current='dashboard';
  function render(view){
    current=view;
    document.querySelectorAll('#sidenav a').forEach(function(a){a.classList.toggle('active',a.getAttribute('data-view')===view);});
    content.innerHTML=(VIEWS[view]||VIEWS.dashboard)();
    window.scrollTo(0,0);
    content.querySelectorAll('[data-view]').forEach(function(elm){var v=elm.getAttribute('data-view'); if(v) elm.addEventListener('click',function(){render(v);});});
    if(view==='explorer'){var b=document.getElementById('expBtn'),i=document.getElementById('expSearch');b.onclick=function(){runExplorer(i.value);};i.addEventListener('keydown',function(e){if(e.key==='Enter')runExplorer(i.value);});}
  }

  function init(){
    var sup=document.getElementById('fSupplier'); D.suppliers.forEach(function(s){var o=document.createElement('option');o.textContent=s[0];sup.appendChild(o);});
    var cont=document.getElementById('fContainer'), seen={}; D.purchaseOrders.forEach(function(r){if(r[2]&&!seen[r[2]]){seen[r[2]]=1;var o=document.createElement('option');o.textContent=r[2];cont.appendChild(o);}});
    document.getElementById('periodInfo').textContent=D.meta.periodLabel;
    document.getElementById('recordsInfo').textContent=n(D.meta.totalRecordsLoaded)+' records loaded';
    document.getElementById('refreshInfo').textContent=D.meta.capturedAt;
    var cb=document.getElementById('collapseBtn'); if(cb) cb.onclick=function(){document.body.classList.toggle('nav-collapsed');};
    document.querySelectorAll('#sidenav a').forEach(function(a){a.addEventListener('click',function(e){e.preventDefault();PAGE={};render(a.getAttribute('data-view'));});});
    ['fSupplier','fContainer','fMarket','fStatus'].forEach(function(id){document.getElementById(id).addEventListener('change',function(){PAGE={};render(current);});});
    var srch=document.getElementById('fSearch');
    srch.addEventListener('keydown',function(e){if(e.key==='Enter'){PAGE={}; if(current==='journey'){render('journey');} else {render('explorer'); setTimeout(function(){var i=document.getElementById('expSearch'); if(i){i.value=srch.value;runExplorer(srch.value);}},0);} }});
    document.getElementById('themeBtn').onclick=function(){var el=document.documentElement; el.setAttribute('data-theme', el.getAttribute('data-theme')==='dark'?'light':'dark');};
    document.getElementById('exportBtn').onclick=exportCsv;
    render('dashboard');
  }
  function exportCsv(){
    var head=['SKU','Description','Supplier','PO','Container','Created','ComboCount','MarketCount','Listing','Status'];
    var rows=[head].concat(D.componentJourney);
    var csv=rows.map(function(r){return r.map(function(c){return '"'+String(c).replace(/"/g,'""')+'"';}).join(',');}).join('\n');
    var a=document.createElement('a');a.href='data:text/csv;charset=utf-8,'+encodeURIComponent(csv);a.download='component_journey_'+D.meta.capturedAt+'.csv';a.click();
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init); else init();
})();