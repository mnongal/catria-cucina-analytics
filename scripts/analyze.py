"""Validate CSVs, derive cent-exact financials, export BI tables and a dashboard."""
from pathlib import Path
import json
import platform
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def load_data():
    return {name:pd.read_csv(ROOT/'data/raw'/f'{name}.csv')
            for name in ['orders','order_items','menu_items','servers']}

def validate(data):
    o,i,m,s = [data[k] for k in ['orders','order_items','menu_items','servers']]
    checks = []
    def check(name, condition):
        if not bool(condition): raise ValueError('Data quality failure: '+name)
        checks.append({'check':name,'result':'PASS'})
    for name,df,key in [('orders',o,'order_id'),('order_items',i,'order_item_id'),
                        ('menu_items',m,'item_id'),('servers',s,'server_id')]:
        check(name+' primary key',df[key].notna().all() and df[key].is_unique)
    check('line order foreign key',i.order_id.isin(o.order_id).all())
    check('line menu foreign key',i.item_id.isin(m.item_id).all())
    check('order server foreign key',o.server_id.isin(s.server_id).all())
    check('every order has lines',o.order_id.isin(i.order_id).all())
    check('unique order and item pair',not i.duplicated(['order_id','item_id']).any())
    check('valid quantity',((i.quantity>=1)&(i.quantity%1==0)).all())
    check('valid snapshot amounts',(i[['unit_price','unit_cost']].notna().all().all()
        and (i.unit_price>0).all() and (i.unit_cost>=0).all()))
    check('valid discounts',o.discount_percent.isin([0,10,20]).all())
    check('valid status',o.status.isin(['completed','cancelled']).all())
    check('valid channel',o.channel.isin(['dine_in','takeaway']).all())
    check('valid payment method',o.payment_method.isin(['Credit Card','Debit Card','Cash']).all())
    check('date coverage',set(o.order_date)==set(pd.date_range('2026-01-01','2026-06-30').strftime('%Y-%m-%d')))
    times=pd.to_datetime(o.order_date+' '+o.order_time)
    check('opening hours',times.dt.hour.between(11,21).all())
    dine=o.channel.eq('dine_in'); done=o.status.eq('completed')
    check('dine-in fields',o.loc[dine,'party_size'].between(1,6).all() and o.loc[dine,'table_number'].between(1,24).all())
    check('takeaway nulls',o.loc[~dine,['party_size','table_number']].isna().all().all())
    check('completed timings',o.loc[done,'service_minutes'].gt(0).all() and
          o.loc[done,'check_duration_minutes'].ge(o.loc[done,'service_minutes']).all())
    check('cancelled timings',o.loc[~done,['service_minutes','check_duration_minutes']].isna().all().all())
    # Check capacity and no overlapping seated checks independently of generator.
    for _,group in o.loc[dine].sort_values(['order_date','order_time']).groupby(['order_date','table_number']):
        starts=pd.to_datetime(group.order_date+' '+group.order_time)
        ends=starts+pd.to_timedelta(group.check_duration_minutes.fillna(5),unit='m')
        if len(group)>1 and not (starts.iloc[1:].to_numpy()>=ends.iloc[:-1].to_numpy()).all():
            raise ValueError('Overlapping table occupancy')
    check('no overlapping table occupancy',True)
    caps=np.where(o.loc[dine,'table_number']<=8,2,np.where(o.loc[dine,'table_number']<=20,4,6))
    check('table capacity',(o.loc[dine,'party_size']<=caps).all())
    return checks

def derive(data):
    o,i,m,s=[data[k] for k in ['orders','order_items','menu_items','servers']]
    # Integer cents avoid floating rounding differences with SQL DECIMAL.
    f=i.merge(o,on='order_id',validate='many_to_one').merge(
        m[['item_id','item_name','category']],on='item_id',validate='many_to_one')
    f=f.loc[f.status.eq('completed')].copy()
    f['gross_cents']=np.rint(f.unit_price*100).astype('int64')*f.quantity
    f['discount_cents']=(f.gross_cents*f.discount_percent+50)//100
    f['net_cents']=f.gross_cents-f.discount_cents
    f['cost_cents']=np.rint(f.unit_cost*100).astype('int64')*f.quantity
    f['contribution_cents']=f.net_cents-f.cost_cents
    amounts=['gross_cents','discount_cents','net_cents','cost_cents','contribution_cents']
    order=f.groupby('order_id',as_index=False)[amounts+['quantity']].sum().merge(
        o,on='order_id',validate='one_to_one').merge(s,on='server_id',validate='many_to_one')
    order['month']=order.order_date.str[:7]
    order['weekday']=pd.to_datetime(order.order_date).dt.dayofweek
    order['hour']=order.order_time.str[:2].astype(int)
    order['discount_band']=np.where(order.discount_percent>0,'discounted','full_price')
    return f,order

def summarize(order,keys):
    q=order.groupby(keys,as_index=False).agg(orders=('order_id','size'),
        gross_cents=('gross_cents','sum'),discount_cents=('discount_cents','sum'),
        net_cents=('net_cents','sum'),cost_cents=('cost_cents','sum'),
        contribution_cents=('contribution_cents','sum'),
        avg_service_minutes=('service_minutes','mean'))
    for base in ['gross','discount','net','cost','contribution']:
        q[base+'_sales' if base in ['gross','net'] else base+'_amount']=q.pop(base+'_cents')/100
    q['aov']=q.net_sales/q.orders
    q['contribution_margin_pct']=q.contribution_amount/q.net_sales*100
    return q

def run():
    data=load_data(); checks=validate(data); f,o=derive(data)
    out=ROOT/'data/processed'; out.mkdir(parents=True,exist_ok=True)
    monthly=summarize(o,['month'])
    monthly['mom_net_sales_pct']=monthly.net_sales.pct_change()*100
    monthly['calendar_days']=pd.to_datetime(monthly.month).dt.days_in_month
    monthly['net_sales_per_day']=monthly.net_sales/monthly.calendar_days
    daily=summarize(o,['order_date'])
    daily['trailing_7d_net_sales']=daily.net_sales.rolling(7,min_periods=7).sum()
    category=f.groupby('category',as_index=False).agg(units=('quantity','sum'),
        net_cents=('net_cents','sum'),contribution_cents=('contribution_cents','sum'))
    category['net_sales']=category.pop('net_cents')/100
    category['contribution_amount']=category.pop('contribution_cents')/100
    category['contribution_margin_pct']=category.contribution_amount/category.net_sales*100
    menu=f.groupby(['item_id','item_name','category'],as_index=False).agg(units=('quantity','sum'),
        net_cents=('net_cents','sum'),contribution_cents=('contribution_cents','sum'))
    menu['net_sales']=menu.pop('net_cents')/100
    menu['contribution_amount']=menu.pop('contribution_cents')/100
    menu['contribution_per_unit']=menu.contribution_amount/menu.units
    menu['contribution_margin_pct']=menu.contribution_amount/menu.net_sales*100
    menu=menu.sort_values(['net_sales','item_id'],ascending=[False,True])
    weekday=summarize(o,['weekday'])
    calendar=pd.DataFrame({'date':pd.date_range('2026-01-01','2026-06-30')})
    weekday['operating_days']=weekday.weekday.map(calendar.date.dt.dayofweek.value_counts())
    weekday['orders_per_day']=weekday.orders/weekday.operating_days
    weekday['day_name']=weekday.weekday.map(dict(enumerate(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])))
    hour=summarize(o,['weekday','hour'])
    hour['operating_days']=hour.weekday.map(calendar.date.dt.dayofweek.value_counts())
    hour['orders_per_operating_hour']=hour.orders/hour.operating_days
    server=summarize(o,['server_id','server_name'])
    server['active_days']=server.server_id.map(o.groupby('server_id').order_date.nunique())
    server['orders_per_active_day']=server.orders/server.active_days
    discounts=summarize(o,['discount_band'])
    channel=summarize(o,['channel'])
    cancel=data['orders'].groupby('channel',as_index=False).agg(recorded_orders=('order_id','size'),
        cancelled_orders=('status',lambda x:x.eq('cancelled').sum()))
    cancel['cancellation_rate_pct']=cancel.cancelled_orders/cancel.recorded_orders*100
    dine=o[o.channel.eq('dine_in')]
    attachment=f.assign(is_beverage=f.category.eq('Beverage')).groupby('order_id').is_beverage.any()
    kpis={'recorded_orders':len(data['orders']),'completed_orders':len(o),
        'cancelled_orders':len(data['orders'])-len(o),'gross_sales':int(o.gross_cents.sum())/100,
        'discount_amount':int(o.discount_cents.sum())/100,'net_sales':int(o.net_cents.sum())/100,
        'ingredient_cost':int(o.cost_cents.sum())/100,'contribution_amount':int(o.contribution_cents.sum())/100,
        'aov':o.net_cents.sum()/100/len(o),'contribution_margin_pct':o.contribution_cents.sum()/o.net_cents.sum()*100,
        'cancellation_rate_pct':(len(data['orders'])-len(o))/len(data['orders'])*100,
        'beverage_attachment_pct':attachment.mean()*100,
        'avg_service_minutes':o.service_minutes.mean(),'dine_in_covers':int(dine.party_size.sum()),
        'dine_in_sales_per_cover':dine.net_cents.sum()/100/dine.party_size.sum(),
        'dine_in_avg_check_duration_minutes':dine.check_duration_minutes.mean()}
    assert int(f.net_cents.sum())==int(o.net_cents.sum())
    assert int(o.gross_cents.sum()-o.discount_cents.sum())==int(o.net_cents.sum())
    assert abs(monthly.net_sales.sum()-kpis['net_sales'])<.001
    assert abs(menu.net_sales.sum()-kpis['net_sales'])<.001
    checks += [{'check':x,'result':'PASS'} for x in ['line to order revenue reconciliation',
        'gross minus discounts equals net','monthly and menu totals reconcile']]
    outputs={'monthly_kpis':monthly,'daily_kpis':daily,'menu_performance':menu,
        'category_performance':category,'weekday_performance':weekday,'hourly_demand':hour,
        'server_performance':server,'discount_performance':discounts,'channel_performance':channel,
        'cancellations':cancel,'order_metrics':o,'line_metrics':f}
    for name,df in outputs.items():
        df.to_csv(out/f'{name}.csv',index=False,float_format='%.6f',lineterminator='\n')
    (out/'kpis.json').write_text(json.dumps(kpis,indent=2)+'\n')
    report={'checks':checks,'python':platform.python_version(),'pandas':pd.__version__,
            'numpy':np.__version__,'mysql_execution':'Not executed in build environment; run scripts/verify_mysql.py against MySQL 8.4.'}
    reports=ROOT/'reports'; reports.mkdir(exist_ok=True)
    (reports/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    from dashboard import render
    render(kpis,monthly,menu,weekday,hour,category)
    print(json.dumps(kpis,indent=2))
    return kpis

if __name__=='__main__': run()
