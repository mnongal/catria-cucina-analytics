"""Behavioral tests and a separate SQL reconciliation, using only a local SQLite DB."""
import sys
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import sqlite3
import tempfile
import hashlib
import unittest
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import analyze
import generate_data

class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=analyze.load_data()
        cls.lines,cls.orders=analyze.derive(cls.data)

    def test_data_contract(self):
        self.assertTrue(analyze.validate(self.data))

    def test_missing_parent_rejected(self):
        data={k:v.copy() for k,v in self.data.items()}
        data['order_items'].loc[0,'order_id']=-1
        with self.assertRaisesRegex(ValueError,'foreign key'): analyze.validate(data)

    def test_duplicate_dimension_rejected(self):
        data={k:v.copy() for k,v in self.data.items()}
        data['menu_items']=pd.concat([data['menu_items'],data['menu_items'].iloc[[0]]])
        with self.assertRaisesRegex(ValueError,'primary key'): analyze.validate(data)

    def test_cancelled_order_economics_excluded(self):
        cancelled=set(self.data['orders'].query("status == 'cancelled'").order_id)
        self.assertTrue(cancelled)
        self.assertFalse(cancelled.intersection(self.lines.order_id))
        self.assertFalse(cancelled.intersection(self.orders.order_id))

    def test_round_half_up_and_snapshot_price(self):
        # Deliberately different menu reference price proves snapshot use.
        data={k:v.iloc[[0]].copy() for k,v in self.data.items()}
        data['orders'].loc[:,'status']='completed'
        data['orders'].loc[:,'discount_percent']=10
        data['order_items'].loc[:,'order_id']=data['orders'].iloc[0].order_id
        data['order_items'].loc[:,'item_id']=data['menu_items'].iloc[0].item_id
        data['orders'].loc[:,'server_id']=data['servers'].iloc[0].server_id
        data['order_items'].loc[:,'quantity']=1
        data['order_items'].loc[:,'unit_price']=2.25
        data['menu_items'].loc[:,'selling_price']=999.0
        lines,_=analyze.derive(data)
        self.assertEqual(int(lines.iloc[0].discount_cents),23)
        self.assertEqual(int(lines.iloc[0].net_cents),202)

    def test_independent_decimal_and_sql_reconciliation(self):
        # Rebuild raw financial amounts with Decimal, not analyze.derive arithmetic.
        records=[]
        orders=self.data['orders'].set_index('order_id')
        for row in self.data['order_items'].itertuples():
            order=orders.loc[row.order_id]
            if order.status!='completed': continue
            gross=Decimal(str(row.unit_price))*int(row.quantity)
            discount=(gross*Decimal(int(order.discount_percent))/100).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
            cost=Decimal(str(row.unit_cost))*int(row.quantity)
            records.append((row.order_id,row.item_id,order.order_date[:7],int((gross-discount)*100),int(cost*100)))
        db=sqlite3.connect(':memory:')
        try:
            db.execute('CREATE TABLE line (order_id INTEGER,item_id INTEGER,month TEXT,net INTEGER,cost INTEGER)')
            db.executemany('INSERT INTO line VALUES (?,?,?,?,?)',records)
            net,cost,count=db.execute('SELECT SUM(net),SUM(cost),COUNT(DISTINCT order_id) FROM line').fetchone()
            self.assertEqual(net,int(self.orders.net_cents.sum()))
            self.assertEqual(cost,int(self.orders.cost_cents.sum()))
            self.assertEqual(count,len(self.orders))
            actual=dict(db.execute('SELECT month,SUM(net) FROM line GROUP BY month').fetchall())
            self.assertEqual(actual,self.orders.groupby('month').net_cents.sum().to_dict())
            actual=dict(db.execute('SELECT item_id,SUM(net) FROM line GROUP BY item_id').fetchall())
            self.assertEqual(actual,self.lines.groupby('item_id').net_cents.sum().to_dict())
        finally: db.close()

    def test_seed_reproduces_delivered_csv_bytes(self):
        original=generate_data.ROOT
        try:
            with tempfile.TemporaryDirectory() as directory:
                generate_data.ROOT=Path(directory)
                generate_data.main()
                for name in self.data:
                    old=ROOT/'data/raw'/f'{name}.csv'
                    new=Path(directory)/'data/raw'/f'{name}.csv'
                    self.assertEqual(hashlib.sha256(old.read_bytes()).hexdigest(),
                                     hashlib.sha256(new.read_bytes()).hexdigest(),name)
        finally: generate_data.ROOT=original

if __name__=='__main__': unittest.main()
