export const CATEGORIES = ['Main', 'Starter', 'Beverage', 'Dessert'];
export const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
export const MONTHS = ['2026-01','2026-02','2026-03','2026-04','2026-05','2026-06'];

export function validateFilters(input) {
  const allowed = {month:['all',...MONTHS], channel:['all','dine_in','takeaway'],category:['all',...CATEGORIES]};
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw new Error('Filters must be an object.');
  for (const [key,value] of Object.entries(input)) {
    if (!allowed[key]?.includes(value)) throw new Error(`Invalid ${key} filter.`);
  }
  return {month:'all',channel:'all',category:'all',...input};
}

export function aggregate(data, input) {
  const filters=validateFilters(input);
  const selectedOrders=data.orders.filter(o => (filters.month==='all'||o[1].startsWith(filters.month)) && (filters.channel==='all'||o[3]===filters.channel));
  const orderMap=new Map(selectedOrders.filter(o=>o[4]==='completed').map(o=>[o[0],o]));
  const menuMap=new Map(data.menu.map(m=>[m[0],m]));
  const dates=[];
  for(let d=new Date(data.period[0]+'T00:00:00Z');d<=new Date(data.period[1]+'T00:00:00Z');d.setUTCDate(d.getUTCDate()+1)) {
    const date=d.toISOString().slice(0,10);
    if(filters.month==='all'||date.startsWith(filters.month)) dates.push(date);
  }
  const weekdays=WEEKDAYS.map((name,i)=>({name,index:i,days:0,orders:0,service:0}));
  const heat=Array.from({length:7},()=>Array.from({length:11},()=>({orders:0,service:0})));
  const trend=new Map();
  for(const date of dates) {
    weekdays[(new Date(date+'T00:00:00Z').getUTCDay()+6)%7].days++;
    const key=filters.month==='all'?date.slice(0,7):date;
    if(!trend.has(key)) trend.set(key,{date:key,net:0,orders:0});
  }
  const items=new Map(), cats=new Map(), matched=new Set();
  let gross=0,discount=0,cost=0,units=0;
  for(const [oid,itemId,quantity,lineGross,lineDiscount,lineCost] of data.lines) {
    const order=orderMap.get(oid), menu=menuMap.get(itemId);
    if(!order || !menu || (filters.category!=='all'&&menu[2]!==filters.category)) continue;
    const net=lineGross-lineDiscount;
    gross+=lineGross; discount+=lineDiscount; cost+=lineCost; units+=quantity;
    matched.add(oid);
    if(!items.has(itemId)) items.set(itemId,{id:itemId,name:menu[1],category:menu[2],units:0,net:0,cost:0});
    const item=items.get(itemId); item.units+=quantity;item.net+=net;item.cost+=lineCost;
    if(!cats.has(menu[2])) cats.set(menu[2],{name:menu[2],net:0,cost:0});
    cats.get(menu[2]).net+=net;cats.get(menu[2]).cost+=lineCost;
    trend.get(filters.month==='all'?order[1].slice(0,7):order[1]).net+=net;
  }
  let service=0;
  for(const oid of matched) {
    const order=orderMap.get(oid),day=(new Date(order[1]+'T00:00:00Z').getUTCDay()+6)%7;
    weekdays[day].orders++;weekdays[day].service+=order[5];service+=order[5];
    const cell=heat[day][order[2]-11];cell.orders++;cell.service+=order[5];
    trend.get(filters.month==='all'?order[1].slice(0,7):order[1]).orders++;
  }
  const net=gross-discount, contribution=net-cost, cancelled=selectedOrders.filter(o=>o[4]==='cancelled').length;
  const result={filters,days:dates.length,orders:matched.size,units,gross,discount,cost,net,contribution,
    aov:matched.size?net/matched.size:null,margin:net?100*contribution/net:null,
    service:matched.size?service/matched.size:null,recorded:selectedOrders.length,cancelled,
    cancellationRate:selectedOrders.length?100*cancelled/selectedOrders.length:null,
    items:[...items.values()].map(i=>({...i,contribution:i.net-i.cost,margin:i.net?100*(i.net-i.cost)/i.net:null})),
    categories:[...cats.values()].map(c=>({...c,contribution:c.net-c.cost,margin:c.net?100*(c.net-c.cost)/c.net:null})),
    weekdays:weekdays.map(w=>({...w,rate:w.days?w.orders/w.days:0,avgService:w.orders?w.service/w.orders:null})),
    heat:heat.map((row,i)=>row.map(c=>({...c,rate:weekdays[i].days?c.orders/weekdays[i].days:0,avgService:c.orders?c.service/c.orders:null}))),
    trend:[...trend.values()]};
  result.items.sort((a,b)=>b.net-a.net||a.id-b.id);
  return result;
}

export function summaryCSV(result) {
  const f=result.filters;
  const rows=[['metric','value','unit'],['period',f.month,'selection'],['channel',f.channel,'selection'],['category',f.category,'selection'],['operating_days',result.days,'days'],['matching_completed_checks',result.orders,'checks'],['net_sales',(result.net/100).toFixed(2),'USD'],['gross_sales',(result.gross/100).toFixed(2),'USD'],['discounts',(result.discount/100).toFixed(2),'USD'],['ingredient_cost',(result.cost/100).toFixed(2),'USD'],['ingredient_contribution',(result.contribution/100).toFixed(2),'USD'],['sales_per_matching_check',result.aov==null?'':(result.aov/100).toFixed(2),'USD'],['contribution_margin',result.margin?.toFixed(4)??'','percent'],['average_service',result.service?.toFixed(4)??'','minutes'],['cancellation_rate_category_ignored',result.cancellationRate?.toFixed(4)??'','percent'],[],['item','category','units','net_sales_usd','contribution_usd','margin_percent'],...result.items.map(i=>[i.name,i.category,i.units,(i.net/100).toFixed(2),(i.contribution/100).toFixed(2),i.margin?.toFixed(4)??''])];
  return rows.map(row=>row.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(',')).join('\r\n');
}
