import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {aggregate,validateFilters,summaryCSV} from '../dist/model.mjs';

const data=JSON.parse(readFileSync(new URL('../dist/data.json',import.meta.url)));
const kpis=JSON.parse(readFileSync(new URL('../data/processed/kpis.json',import.meta.url)));
const all=aggregate(data,{});
assert.equal(all.orders,kpis.completed_orders);
assert.equal(all.net,Math.round(kpis.net_sales*100));
assert.equal(all.cost,Math.round(kpis.ingredient_cost*100));
assert.equal(all.discount,Math.round(kpis.discount_amount*100));
assert.equal(all.days,181);
assert.equal(all.cancelled,242);
assert.equal(all.trend.reduce((s,r)=>s+r.net,0),all.net);
assert.equal(all.weekdays.reduce((s,r)=>s+r.orders,0),all.orders);
assert.equal(all.heat.flat().reduce((s,r)=>s+r.orders,0),all.orders);
assert.ok(Math.abs(all.service-kpis.avg_service_minutes)<1e-9);
assert.equal(aggregate(data,{month:'2026-02'}).days,28);
assert.equal(aggregate(data,{month:'2026-02'}).net,15362130);
assert.equal(aggregate(data,{category:'Beverage'}).net,16794111);
assert.equal(aggregate(data,{category:'Main'}).net,83282794);
assert.equal(aggregate(data,{category:'Main'}).orders,14860);

// Independent raw CSV reference for a combined month/channel/category filter.
function readCSV(name) {
  const [header,...lines]=readFileSync(new URL(`../data/raw/${name}.csv`,import.meta.url),'utf8').trim().split(/\r?\n/);
  const keys=header.split(',');
  return lines.map(line=>Object.fromEntries(line.split(',').map((value,i)=>[keys[i],value])));
}
const selected=new Map(readCSV('orders').filter(o=>o.status==='completed'&&o.channel==='takeaway'&&o.order_date.startsWith('2026-04')).map(o=>[Number(o.order_id),o]));
const dessertIds=new Set(readCSV('menu_items').filter(i=>i.category==='Dessert').map(i=>Number(i.item_id)));
const matched=new Set();let expectedNet=0;
for(const row of readCSV('order_items')) {
  const o=selected.get(Number(row.order_id));
  if(!o||!dessertIds.has(Number(row.item_id)))continue;
  const gross=Math.round(Number(row.unit_price)*100)*Number(row.quantity);
  expectedNet+=gross-Math.floor((gross*Number(o.discount_percent)+50)/100);
  matched.add(Number(row.order_id));
}
const filtered=aggregate(data,{month:'2026-04',channel:'takeaway',category:'Dessert'});
assert.equal(filtered.net,expectedNet);
assert.equal(filtered.orders,matched.size);
assert.equal(filtered.trend.length,30);
assert.equal(filtered.recorded,aggregate(data,{month:'2026-04',channel:'takeaway'}).recorded);
assert.ok(filtered.items.every(i=>i.category==='Dessert'));
assert.throws(()=>validateFilters({month:'2025-10'}));
assert.throws(()=>validateFilters({category:'Invalid'}));
assert.throws(()=>validateFilters({unexpected:true}));
const empty=aggregate({...data,lines:[]},{});
assert.equal(empty.net,0);assert.equal(empty.orders,0);assert.equal(empty.aov,null);assert.equal(empty.margin,null);
assert.ok(summaryCSV(all).includes('"net_sales","1126292.82","USD"'));
assert.ok(summaryCSV(filtered).includes('"category","Dessert","selection"'));
assert.ok(summaryCSV(filtered).includes('"net_sales","1195.16","USD"'));
assert.ok(summaryCSV({...filtered,items:[{...filtered.items[0],name:'A "quoted", item'}]}).includes('"A ""quoted"", item"'));
console.log('PASS: baseline financials, counts, time denominators, combined filters, raw-data reconciliation, invalid filters and empty states.');
console.log('PASS: summary CSV totals, filter metadata and field escaping.');
