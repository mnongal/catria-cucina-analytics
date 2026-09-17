"""Read-only MySQL/Pandas parity check. Run after importing CSVs and creating views."""
from pathlib import Path
import argparse
import getpass
import json
import re
from datetime import datetime, timezone
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def statements(path):
    sql=re.sub(r'--[^\n]*','',path.read_text())
    return [s.strip() for s in sql.split(';') if s.strip() and not s.strip().upper().startswith('USE ')]

def main():
    import mysql.connector
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--user',required=True);p.add_argument('--host',default='127.0.0.1')
    p.add_argument('--port',type=int,default=3306);p.add_argument('--database',default='restaurant_analytics')
    args=p.parse_args()
    connection=mysql.connector.connect(host=args.host,port=args.port,user=args.user,
        password=getpass.getpass('MySQL password: '),database=args.database)
    cur=connection.cursor()
    # Increase division precision so ratios can be compared to Python precisely.
    cur.execute('SET SESSION div_precision_increment=10')
    cur.execute('SELECT VERSION()');version=cur.fetchone()[0]
    manifest=json.loads((ROOT/'data/raw/manifest.json').read_text())
    checks=[]
    try:
        for table,count in manifest['row_counts'].items():
            if table not in ['orders','order_items','menu_items','servers']: raise ValueError(table)
            cur.execute(f'SELECT COUNT(*) FROM `{table}`')
            assert cur.fetchone()[0]==count, f'{table}: row count mismatch'
            checks.append({'check':table+' count','result':'PASS'})
        k=json.loads((ROOT/'data/processed/kpis.json').read_text())
        files=[None,'monthly_kpis','menu_performance','category_performance','weekday_performance',
               'hourly_demand','server_performance','discount_performance','channel_performance',
               'cancellations','daily_kpis',None,None]
        queries=statements(ROOT/'sql/04_analysis.sql')
        assert len(queries)==13
        for index,(sql,name) in enumerate(zip(queries,files),1):
            cur.execute(sql)
            actual=pd.DataFrame(cur.fetchall(),columns=[c[0] for c in cur.description])
            expected=pd.read_csv(ROOT/'data/processed'/f'{name}.csv') if name else pd.DataFrame([k])
            expected=expected[list(actual.columns)]
            assert len(actual)==len(expected),f'Q{index:02}: number of rows'
            for col in actual.columns:
                if col in ['month','item_name','category','server_name','discount_band','channel','order_date']:
                    assert actual[col].astype(str).tolist()==expected[col].astype(str).tolist(),f'Q{index:02}: {col}'
                else:
                    a=pd.to_numeric(actual[col]).to_numpy(dtype=float)
                    b=pd.to_numeric(expected[col]).to_numpy(dtype=float)
                    np.testing.assert_allclose(a,b,rtol=0,atol=1e-5,equal_nan=True,
                                               err_msg=f'Q{index:02}: {col}')
            checks.append({'check':f'Q{index:02} SQL/Pandas comparison','result':'PASS','rows':len(actual)})
        result={'executed_at_utc':datetime.now(timezone.utc).isoformat(),'mysql_version':version,'checks':checks}
        (ROOT/'reports/mysql_validation.json').write_text(json.dumps(result,indent=2)+'\n')
        print('PASS: four table counts and all 13 SQL analyses match Python outputs.')
    finally:
        cur.close();connection.close()

if __name__=='__main__': main()
