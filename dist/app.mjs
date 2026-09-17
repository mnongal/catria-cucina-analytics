import {aggregate,validateFilters,summaryCSV,CATEGORIES,WEEKDAYS,MONTHS} from './model.mjs';

const $=id=>document.getElementById(id);
const COLORS={Main:'#087f70',Starter:'#bc7315',Beverage:'#5c77be',Dessert:'#b26078'};
const money=cents=>cents==null?'—':new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(cents/100);
const exactMoney=cents=>cents==null?'—':new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',minimumFractionDigits:2,maximumFractionDigits:2}).format(cents/100);
const compact=cents=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',notation:'compact',maximumFractionDigits:1}).format(cents/100);
const number=n=>new Intl.NumberFormat('en-US').format(n);
const percent=n=>n==null?'—':n.toFixed(1)+'%';
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const names={overview:['Overview','Every check tells a story.','Explore what sells, when demand peaks, and what stays after ingredient costs.'],menu:['Menu performance','What earns its place on the menu?','Compare sales, volume, and ingredient contribution for every dish and drink.'],operations:['Operations','Find the rhythm of the restaurant.','See when checks arrive and where service demand is concentrated.'],insights:['Findings & methods','From numbers to better questions.','Business interpretations, proposed tests, and the assumptions behind this case.']};
let dataset,result,filters={month:'all',channel:'all',category:'all'};

function showView(view) {
  if(!names[view]) view='overview';
  document.querySelectorAll('.view').forEach(el=>el.hidden=el.id!==`view-${view}`);
  document.querySelectorAll('.nav-item').forEach(el=>{
    const active=el.dataset.view===view;el.classList.toggle('active',active);
    if(active)el.setAttribute('aria-current','page');else el.removeAttribute('aria-current');
  });
  [$('breadcrumb').textContent,$('page-title').textContent,$('page-subtitle').textContent]=names[view];
  const url=new URL(location.href);url.hash=view;history.replaceState(null,'',url);
  if(view==='overview'&&result)renderSales();
}

function renderSales() {
  const w=Math.max(300,$('sales-chart').clientWidth),h=244,left=52,right=15,top=24,bottom=39;
  const pw=w-left-right,ph=h-top-bottom;
  const max=Math.max(100,...result.trend.map(r=>r.net))*1.12;
  const count=result.trend.length,bw=pw/count,bar=Math.min(45,bw*.62);
  let html=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-labelledby="sales-title sales-desc"><title id="sales-title">Net sales over time</title><desc id="sales-desc">${esc(result.trend.map(p=>`${p.date}: ${exactMoney(p.net)}`).join('; '))}</desc>`;
  for(let j=0;j<=3;j++) {
    const value=max*j/3,y=top+ph-ph*j/3;
    html+=`<line x1="${left}" y1="${y}" x2="${w-right}" y2="${y}" stroke="#e5ecef" stroke-dasharray="3 4"/><text x="${left-10}" y="${y+4}" text-anchor="end">${compact(value)}</text>`;
  }
  result.trend.forEach((p,i)=>{
    const bh=p.net/max*ph,x=left+bw*i+(bw-bar)/2,y=top+ph-bh;
    const label=count===6?new Date(p.date+'-01T00:00:00Z').toLocaleDateString('en-US',{month:'short',timeZone:'UTC'}):String(Number(p.date.slice(-2)));
    html+=`<rect x="${x}" y="${y}" width="${bar}" height="${Math.max(.3,bh)}" rx="3" fill="${i===count-1?'#087f70':'#a9d8c9'}"><title>${esc(p.date)}: ${exactMoney(p.net)} · ${p.orders} checks</title></rect>`;
    if(count===6&&w>=430) html+=`<text x="${x+bar/2}" y="${y-9}" text-anchor="middle" style="fill:#264f49;font-weight:600">${compact(p.net)}</text>`;
    if(count===6||i%5===0||i===count-1) html+=`<text x="${x+bar/2}" y="${h-12}" text-anchor="middle">${label}</text>`;
  });
  $('sales-chart').innerHTML=html+'</svg>';
  $('trend-foot').textContent=filters.month==='all'?'Monthly totals · January–June 2026':'Daily totals · '+$('month').selectedOptions[0].textContent;
}

function renderMix() {
  let offset=0;
  const cats=result.categories.sort((a,b)=>b.net-a.net);
  const circles=cats.map(c=>{
    const fraction=result.net?c.net/result.net:0;
    const circle=`<circle cx="80" cy="80" r="64" pathLength="100" fill="none" stroke="${COLORS[c.name]}" stroke-width="18" stroke-dasharray="${fraction*100} ${100-fraction*100}" stroke-dashoffset="${-offset}"/>`;
    offset+=fraction*100;return circle;
  }).join('');
  $('mix-chart').innerHTML=`<div class="mix-chart-wrap"><svg viewBox="0 0 160 160" role="img" aria-label="${esc(cats.map(c=>`${c.name}: ${percent(result.net?100*c.net/result.net:0)} of net sales`).join('; '))}"><circle cx="80" cy="80" r="64" fill="none" stroke="#eef3f4" stroke-width="18"/>${circles}</svg><div class="mix-center"><strong>${compact(result.net)}</strong><span>net sales</span></div></div>`;
  $('mix-legend').innerHTML=cats.map(c=>`<div><i style="background:${COLORS[c.name]}"></i><span>${c.name==='Main'?'Mains':c.name==='Beverage'?'Beverages':c.name+'s'}</span><strong>${percent(result.net?100*c.net/result.net:0)}</strong></div>`).join('');
}

function renderRanking() {
  const top=result.items.slice(0,5),max=top[0]?.net||1;
  $('top-menu').innerHTML=top.length?top.map((m,i)=>`<div class="rank-row"><span class="rank-number">0${i+1}</span><div><div class="rank-title"><span>${esc(m.name)}</span><strong>${compact(m.net)}</strong></div><div class="rank-track" aria-hidden="true"><div class="rank-fill" style="width:${m.net/max*100}%"></div></div></div></div>`).join(''):'<p class="empty">No items match these filters.</p>';
}

function renderWeekdays() {
  const max=Math.max(1,...result.weekdays.map(w=>w.rate));
  $('weekday-chart').innerHTML=result.weekdays.map(w=>`<div class="day-column ${w.rate===max?'peak':''}" role="img" aria-label="${w.name}: ${w.rate.toFixed(1)} checks per operating day"><strong>${w.rate.toFixed(1)}</strong><div class="bar" style="height:${w.rate/max*143}px"></div><span>${w.name.slice(0,3)}</span></div>`).join('');
  const best=[...result.weekdays].sort((a,b)=>b.rate-a.rate)[0];
  $('busiest').textContent=best.name;
  $('busiest-note').textContent=`${best.rate.toFixed(1)} matching checks per operating day`;
  $('insight-title').textContent=`${best.name} leads this selection with ${best.rate.toFixed(1)} checks per day.`;
  $('insight-copy').textContent='Use the demand pattern to plan a service trial. Staffing hours and costs are needed before making a headcount decision.';
}

function renderMenu() {
  if(!result)return;
  const sort=$('menu-sort').value,term=$('menu-search').value.trim().toLowerCase();
  const items=result.items.filter(i=>i.name.toLowerCase().includes(term)).sort((a,b)=>b[sort]-a[sort]||a.id-b.id);
  $('menu-table').innerHTML=items.length?items.map(i=>`<tr><td>${esc(i.name)}</td><td><span class="category-tag">${i.category}</span></td><td class="number">${number(i.units)}</td><td class="number">${exactMoney(i.net)}</td><td class="number">${exactMoney(i.contribution)}</td><td class="number">${percent(i.margin)}</td></tr>`).join(''):'<tr><td colspan="6" class="empty">No menu items match your search. Try another name or reset the filters.</td></tr>';
  $('menu-count').textContent=`${items.length} of ${result.items.length} matching menu items · Contribution excludes operating expenses.`;
}

function renderHeatmap() {
  const max=Math.max(1,...result.heat.flat().map(c=>c.rate));
  $('heatmap').innerHTML=`<table class="heat-table"><caption class="sr-only">Completed checks per weekday and hour</caption><thead><tr><th scope="col">Day</th>${Array.from({length:11},(_,i)=>`<th scope="col">${i+11}:00</th>`).join('')}</tr></thead><tbody>${result.heat.map((row,day)=>`<tr><th scope="row">${WEEKDAYS[day].slice(0,3)}</th>${row.map((c,h)=>{
    const ratio=c.rate/max;const bg=`rgb(${Math.round(236-228*ratio)},${Math.round(246-119*ratio)},${Math.round(242-130*ratio)})`;
    const description=`${WEEKDAYS[day]} ${h+11}:00: ${c.rate.toFixed(1)} checks per operating day; ${c.orders} checks total; average service ${c.avgService==null?'unavailable':c.avgService.toFixed(1)+' minutes'}`;
    return `<td><span class="heat-cell" tabindex="0" title="${description}" aria-label="${description}" style="background:${bg};color:${ratio>.62?'#fff':'#173d36'}">${c.rate.toFixed(1)}</span></td>`;
  }).join('')}</tr>`).join('')}</tbody></table>`;
}

function render() {
  result=aggregate(dataset,filters);
  $('app-content').hidden=false;
  $('net').textContent=money(result.net);$('net').title=exactMoney(result.net);
  $('orders').textContent=number(result.orders);
  $('aov').textContent=exactMoney(result.aov);$('margin').textContent=percent(result.margin);
  const category=filters.category!=='all';
  $('orders-label').textContent=category?'MATCHING CHECKS':'COMPLETED CHECKS';
  $('orders-note').textContent=category?'Distinct checks with selected items':'Cancelled checks excluded';
  $('aov-label').textContent=category?'CATEGORY SPEND / CHECK':'AVERAGE CHECK';
  $('aov-note').textContent=category?'Selected item sales per matching check':'Net sales per completed check';
  $('scope').textContent=category?`${$('month').selectedOptions[0].textContent} · ${$('channel').selectedOptions[0].textContent} · ${filters.category} items only. Check counts and service refer to checks containing these items.`:`${$('month').selectedOptions[0].textContent} · ${$('channel').selectedOptions[0].textContent} · Entire menu · ${result.days} operating days`;
  $('scope').hidden=false;
  $('service').textContent=result.service==null?'—':result.service.toFixed(1)+' min';
  $('cancel-rate').textContent=percent(result.cancellationRate);
  $('cancel-note').textContent=`${number(result.cancelled)} / ${number(result.recorded)} recorded checks · Category ignored`;
  renderSales();renderMix();renderRanking();renderWeekdays();renderMenu();renderHeatmap();
  const url=new URL(location.href);
  for(const [key,value] of Object.entries(filters)) {if(value==='all')url.searchParams.delete(key);else url.searchParams.set(key,value);}
  history.replaceState(null,'',url);
  $('app-content').hidden=false;$('export-button').disabled=false;
  $('status').textContent='';
}

function setFilters(input) {
  const validated=validateFilters(input);
  filters=validated;
  for(const key of Object.keys(filters)) $(key).value=filters[key];
  render();
}

function exportSummary() {
  if(!result)return;
  const csv=summaryCSV(result);
  const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
  const link=document.createElement('a');link.href=url;link.download=`catria-cucina-${filters.month}-${filters.channel}-${filters.category}.csv`;link.hidden=true;document.body.append(link);link.click();link.remove();
  setTimeout(()=>URL.revokeObjectURL(url),30000);
}

function registerTools() {
  const context=document.modelContext;
  if(!context?.registerTool)return;
  const lifecycle=new AbortController();
  const tools=[{
    name:'set_restaurant_filters',title:'Filter restaurant dashboard',
    description:'Set period, dining channel and menu category on the visible restaurant dashboard. Omitted filters reset to all.',
    inputSchema:{type:'object',properties:{month:{type:'string',enum:['all',...MONTHS]},channel:{type:'string',enum:['all','dine_in','takeaway']},category:{type:'string',enum:['all',...CATEGORIES]}},additionalProperties:false},
    annotations:{readOnlyHint:false,untrustedContentHint:false},
    execute(input){setFilters(input);return summary();}
  },{name:'read_restaurant_summary',title:'Read restaurant dashboard summary',description:'Read the metrics for the current visible filters. Monetary values are USD; data are synthetic.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true,untrustedContentHint:false},execute(){return summary();}}];
  for(const tool of tools)try{Promise.resolve(context.registerTool(tool,{signal:lifecycle.signal})).catch(()=>{});}catch{}
  addEventListener('pagehide',()=>lifecycle.abort(),{once:true});
}

function summary(){return {filters:result.filters,completedChecks:result.orders,netSalesUSD:result.net/100,ingredientContributionUSD:result.contribution/100,contributionMarginPercent:result.margin,averageServiceMinutes:result.service,synthetic:true};}

async function init() {
  try {
    const response=await fetch('./data.json');if(!response.ok)throw new Error('Data unavailable');
    dataset=await response.json();
    if(!Array.isArray(dataset.orders)||!Array.isArray(dataset.lines)||!Array.isArray(dataset.menu))throw new Error('Invalid dataset');
    const params=new URL(location.href).searchParams;
    for(const key of ['month','channel','category']) {
      if(params.has(key)){try{validateFilters({[key]:params.get(key)});filters[key]=params.get(key);}catch{}}
    }
    setFilters(filters);registerTools();
    let repository=dataset.repository;
    if(!repository&&location.hostname.endsWith('.github.io')) {
      const user=location.hostname.slice(0,-10),repo=location.pathname.split('/').filter(Boolean)[0]||user+'.github.io';
      repository=`${user}/${repo}`;
    }
    if(/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repository)) {
      for(const id of ['github-link','dialog-github']){$(id).href='https://github.com/'+repository;$(id).hidden=false;}
    }
  }catch(error) {
    $('status').innerHTML='<div class="error"><strong>The dataset could not be loaded.</strong><p>Refresh the page to try again. For local use, open this site through the preview server described in the project guide.</p><button class="button" id="retry">Try again</button></div>';
    $('retry').addEventListener('click',()=>{$('status').textContent='Loading the restaurant dataset…';init();});
  }
}

document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>showView(b.dataset.view)));
document.querySelectorAll('[data-go]').forEach(b=>b.addEventListener('click',()=>{showView(b.dataset.go);$('page-title').scrollIntoView({block:'start'});}));
document.querySelector('.brand').addEventListener('click',e=>{e.preventDefault();showView('overview');});
$('filters').addEventListener('submit',e=>e.preventDefault());
for(const key of ['month','channel','category'])$(key).addEventListener('change',()=>{if(dataset)setFilters(Object.fromEntries(['month','channel','category'].map(k=>[k,$(k).value])));});
$('reset').addEventListener('click',()=>{if(dataset)setFilters({});});
$('menu-search').addEventListener('input',renderMenu);$('menu-sort').addEventListener('change',renderMenu);
$('export-button').addEventListener('click',exportSummary);
const dialog=$('source-dialog');
$('source-button').addEventListener('click',()=>dialog.showModal());
$('mobile-project').addEventListener('click',()=>dialog.showModal());
$('close-dialog').addEventListener('click',()=>dialog.close());
dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});
showView(location.hash.slice(1));
let resizeTimer;
addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>{if(result)renderSales();},100);});
init();
