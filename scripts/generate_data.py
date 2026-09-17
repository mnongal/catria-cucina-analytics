"""Create fictional POS data. Fixed seed; no external data or personal information."""
from pathlib import Path
from collections import Counter
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SEED = 20260101

def main():
    rng = np.random.default_rng(SEED)
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    menu = pd.DataFrame([
        (101,'Margherita Pizza','Main',1800,550),
        (102,'Truffle Pasta','Main',2400,900),
        (103,'Classic Burger','Main',1700,600),
        (104,'Grilled Salmon','Main',2800,1200),
        (105,'Chicken Bowl','Main',1900,650),
        (106,'Mushroom Risotto','Main',2200,750),
        (107,'Steak Frites','Main',3200,1450),
        (108,'Veggie Flatbread','Main',1650,500),
        (201,'Garden Salad','Starter',850,250),
        (202,'Garlic Bread','Starter',650,150),
        (203,'Tomato Soup','Starter',750,200),
        (204,'Crispy Calamari','Starter',1200,480),
        (301,'Lemonade','Beverage',500,90),
        (302,'Iced Tea','Beverage',400,60),
        (303,'House Wine','Beverage',950,300),
        (304,'Craft Beer','Beverage',750,250),
        (305,'Sparkling Water','Beverage',450,100),
        (306,'Espresso','Beverage',350,55),
        (401,'Chocolate Brownie','Dessert',800,220),
        (402,'Tiramisu','Dessert',900,300),
        (403,'Vanilla Gelato','Dessert',600,160),
        (404,'Lemon Tart','Dessert',850,260),
    ], columns=['item_id','item_name','category','price_cents','cost_cents'])
    servers = pd.DataFrame([(i,f'Server {i:02d}') for i in range(1,13)],
                           columns=['server_id','server_name'])
    orders, lines = [], []
    by_id = menu.set_index('item_id')
    order_id = 100001
    for day in pd.date_range('2026-01-01','2026-06-30'):
        weekday = day.dayofweek
        # Designed patterns, not estimates from a real restaurant.
        demand = 69 * [0.80,0.83,0.95,1.08,1.43,1.65,1.20][weekday]
        demand *= [0.92,0.96,1.04,1.08,1.16,1.20][day.month-1]
        n = rng.poisson(demand)
        hours = rng.choice(list(range(11,22)), n,
                           p=[.06,.10,.10,.06,.03,.04,.11,.17,.17,.10,.06])
        minutes = sorted(int(h)*60 + int(rng.integers(0,60)) for h in hours)
        free_at = {t:0 for t in range(1,25)}
        capacities = {t:2 if t<=8 else 4 if t<=20 else 6 for t in free_at}
        # Six rotating staff handle both seated checks and takeaway transactions.
        roster = [((day.dayofyear + j) % 12)+1 for j in range(6)]
        for minute in minutes:
            channel = 'dine_in' if rng.random()<.73 else 'takeaway'
            people = int(rng.choice([1,2,3,4,5,6],p=[.12,.42,.17,.21,.05,.03]))
            cancelled = rng.random() < (.026 if channel=='takeaway' else .013)
            status = 'cancelled' if cancelled else 'completed'
            table = None
            if channel=='dine_in':
                available = [t for t in free_at if free_at[t]<=minute and capacities[t]>=people]
                if not available:
                    continue  # no recorded check when no fitting table is available
                table = min(available, key=lambda t: (capacities[t],t))
            peak = (minute//60 in (18,19)) and weekday in (4,5)
            service = max(7,int(rng.normal(19 + 8*peak + 3*(channel=='takeaway'),4)))
            duration = max(service+15,int(rng.normal(67,13))) if channel=='dine_in' else service
            if table is not None:
                free_at[table] = minute + (5 if cancelled else duration)
            discount = int(rng.choice([0,10,20], p=[.65,.28,.07] if weekday<3 else [.87,.11,.02]))
            server = roster[int(rng.integers(0,len(roster)))]
            orders.append([order_id,str(day.date()),f'{minute//60:02d}:{minute%60:02d}:00',
                server,table,people if channel=='dine_in' else None,channel,status,discount,
                str(rng.choice(['Credit Card','Debit Card','Cash'],p=[.60,.25,.15])),
                None if cancelled else service, None if cancelled else duration])
            basket = Counter()
            for _ in range(people):
                basket[int(rng.choice(range(101,109),p=[.22,.12,.19,.08,.16,.09,.05,.09]))]+=1
                if rng.random() < (.81 if channel=='dine_in' else .43):
                    basket[int(rng.choice(range(301,307),p=[.24,.22,.19,.15,.13,.07]))]+=1
            for _ in range(max(1,people//2)):
                if rng.random()<.48: basket[int(rng.choice(range(201,205)))]+=1
                if rng.random()<(.34 if channel=='dine_in' else .16):
                    basket[int(rng.choice(range(401,405)))]+=1
            for item,quantity in sorted(basket.items()):
                row = by_id.loc[item]
                # Price snapshot: +5%, rounded to nearest $0.25, from April.
                price = int(np.floor(row.price_cents * (1.05 if day.month>=4 else 1)/25+.5))*25
                # Ingredient inflation: +4%, rounded half up to cents, from May.
                cost = int(np.floor(row.cost_cents*(1.04 if day.month>=5 else 1)+.5))
                lines.append([len(lines)+1,order_id,item,quantity,price/100,cost/100])
            order_id += 1
    o = pd.DataFrame(orders, columns=['order_id','order_date','order_time','server_id',
        'table_number','party_size','channel','status','discount_percent','payment_method',
        'service_minutes','check_duration_minutes'])
    for c in ['table_number','party_size','service_minutes','check_duration_minutes']:
        o[c]=o[c].astype('Int64')
    items = pd.DataFrame(lines,columns=['order_item_id','order_id','item_id','quantity',
                                      'unit_price','unit_cost'])
    menu['selling_price'] = np.floor(menu.price_cents*1.05/25+.5)*25/100
    menu['unit_cost'] = np.floor(menu.cost_cents*1.04+.5)/100
    menu = menu.drop(columns=['price_cents','cost_cents'])
    tables = {'servers':servers,'menu_items':menu,'orders':o,'order_items':items}
    for name,df in tables.items():
        df.to_csv(raw/f'{name}.csv',index=False,float_format='%.2f',lineterminator='\n')
    (raw/'manifest.json').write_text(json.dumps({'seed':SEED,'start':'2026-01-01',
        'end':'2026-06-30','source':'synthetic; generated locally',
        'row_counts':{k:len(v) for k,v in tables.items()}},indent=2)+'\n')
    print({k:len(v) for k,v in tables.items()})

if __name__=='__main__': main()
