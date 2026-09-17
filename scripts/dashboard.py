"""Render a portable PNG dashboard using Pillow (no web service required)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]

def render(k,monthly,menu,weekday,hour,category):
    im=Image.new('RGB',(1800,1320),'#eef3f6'); d=ImageDraw.Draw(im)
    def font(size,bold=False):
        candidates=[ROOT/'assets'/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'),
            Path('C:/Windows/Fonts')/('arialbd.ttf' if bold else 'arial.ttf'),
            Path('/usr/share/fonts/truetype/dejavu')/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')]
        for p in candidates:
            if p.exists(): return ImageFont.truetype(str(p),size)
        return ImageFont.load_default(size=size)
    def text(x,y,t,size=22,color='#173348',bold=False): d.text((x,y),str(t),font=font(size,bold),fill=color)
    def panel(box,title,subtitle):
        d.rounded_rectangle(box,18,fill='white'); text(box[0]+24,box[1]+20,title,26,bold=True)
        text(box[0]+24,box[1]+58,subtitle,18,'#536b7b')
    d.rectangle((0,0,1800,166),fill='#123447')
    text(52,26,'CATRIA & CUCINA',20,'#72d2c6',True)
    text(52,60,'Restaurant Revenue & Operations',42,'white',True)
    text(52,119,'JAN - JUN 2026  |  One fictional location  |  USD  |  Synthetic portfolio dataset',21,'#d3e2ea')
    cards=[('NET SALES',f"${k['net_sales']:,.0f}",'After line-level discounts'),
        ('COMPLETED ORDERS',f"{k['completed_orders']:,}",f"{k['cancellation_rate_pct']:.1f}% of recorded checks cancelled"),
        ('AVERAGE ORDER VALUE',f"${k['aov']:.2f}",'Net sales / completed orders'),
        ('INGREDIENT CONTRIBUTION',f"{k['contribution_margin_pct']:.1f}%",'Before labor, rent and other expenses')]
    for j,(label,value,note) in enumerate(cards):
        x=48+j*438; d.rounded_rectangle((x,192,x+414,340),14,fill='white')
        text(x+22,211,label,18,'#536b7b',True);text(x+22,241,value,40,bold=True)
        text(x+22,303,note,16,'#536b7b')
    panel((48,366,880,752),'Monthly net sales','Total sales; calendar-month lengths differ')
    maxv=monthly.net_sales.max()*1.12
    for j,r in monthly.iterrows():
        x=109+j*126; top=682-r.net_sales/maxv*220
        d.rounded_rectangle((x,top,x+68,682),6,fill='#178c88')
        text(x-12,top-31,f'${r.net_sales/1000:.1f}k',20,bold=True)
        text(x+3,697,r.month[5:],20)
    panel((904,366,1752,752),'Top five menu items by net sales','Ranked on completed checks; historical transaction prices')
    top=menu.head(5);maxv=top.net_sales.max()
    for j,r in enumerate(top.itertuples()):
        y=464+j*50;text(928,y,r.item_name,20)
        d.rounded_rectangle((1165,y,1165+405*r.net_sales/maxv,y+27),4,fill='#178c88')
        text(1584,y,f'${r.net_sales/1000:.1f}k',20)
    panel((48,778,880,1186),'Demand by weekday','Completed orders per operating day; all 181 days open')
    maxv=weekday.orders_per_day.max()*1.13
    for j,r in enumerate(weekday.itertuples()):
        x=100+j*108;top=1105-r.orders_per_day/maxv*217
        d.rounded_rectangle((x,top,x+60,1105),5,fill='#e8a34a' if j>=4 else '#178c88')
        text(x+5,top-31,f'{r.orders_per_day:.0f}',21,bold=True);text(x,1123,r.day_name[:3],20)
    panel((904,778,1752,1186),'Category contribution margin','(Net sales - ingredient cost) / net sales')
    for j,r in enumerate(category.sort_values('contribution_margin_pct',ascending=False).itertuples()):
        y=880+j*60;text(928,y,r.category,22)
        d.rounded_rectangle((1100,y,1100+490*r.contribution_margin_pct/100,y+30),4,fill='#178c88')
        text(1606,y,f'{r.contribution_margin_pct:.1f}%',22)
    text(52,1211,'READ WITH CONTEXT',18,bold=True)
    text(52,1244,'Simulated patterns are designed assumptions. Contribution excludes labor, waste, rent, tax, tips and fees.',22)
    text(52,1275,'Discount comparisons are descriptive. Server sales are not productivity rankings without staffing and section data.',20,'#536b7b')
    out=ROOT/'reports/figures';out.mkdir(parents=True,exist_ok=True)
    im.save(out/'dashboard.png')

if __name__=='__main__':
    from analyze import run
    run()
