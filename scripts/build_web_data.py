"""Build portable website data directly from raw CSVs; Python standard library only."""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import csv
import json
import os
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def build():
    raw = ROOT / 'data/raw'
    out = ROOT / 'dist'
    out.mkdir(exist_ok=True)
    def rows(name):
        with (raw / f'{name}.csv').open(encoding='utf-8', newline='') as f:
            return list(csv.DictReader(f))
    def cents(value):
        return int((Decimal(value)*100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    raw_orders = rows('orders')
    order_map = {int(o['order_id']): o for o in raw_orders}
    orders = [[int(o['order_id']), o['order_date'], int(o['order_time'][:2]),
               o['channel'], o['status'], int(o['service_minutes']) if o['service_minutes'] else None,
               int(o['party_size']) if o['party_size'] else None] for o in raw_orders]
    menu = [[int(m['item_id']), m['item_name'], m['category']] for m in rows('menu_items')]
    lines = []
    for i in rows('order_items'):
        oid = int(i['order_id'])
        o = order_map[oid]
        if o['status'] != 'completed':
            continue
        quantity = int(i['quantity'])
        gross = cents(i['unit_price'])*quantity
        discount = (gross*int(o['discount_percent'])+50)//100
        cost = cents(i['unit_cost'])*quantity
        lines.append([oid, int(i['item_id']), quantity, gross, discount, cost])
    data = {'period': ['2026-01-01', '2026-06-30'],
            'repository': os.environ.get('GITHUB_REPOSITORY', ''),
            'orderColumns': ['id','date','hour','channel','status','serviceMinutes','covers'],
            'lineColumns': ['orderId','itemId','quantity','grossCents','discountCents','costCents'],
            'menuColumns': ['id','name','category'],
            'orders': orders, 'lines': lines, 'menu': menu}
    (out/'data.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
    downloads=out/'downloads'
    downloads.mkdir(exist_ok=True)
    with zipfile.ZipFile(downloads/'restaurant-dataset.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(raw.glob('*.csv')):
            z.write(p,p.name)
        z.write(ROOT/'docs/DATA_DICTIONARY.md','DATA_DICTIONARY.md')
        z.write(raw/'manifest.json','manifest.json')
    shutil.copyfile(ROOT/'sql/04_analysis.sql',downloads/'analysis.sql')
    shutil.copyfile(ROOT/'docs/METHODOLOGY.md',downloads/'methodology.md')
    assert sum(l[3]-l[4] for l in lines)==112629282, 'Unexpected baseline revenue; review changed data before publishing.'
    print(f'Website data: {len(orders):,} checks, {len(lines):,} completed item lines.')

if __name__=='__main__':
    build()
