
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import sqlite3, csv, json, html, os
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "customer_analytics.db"
CSV_FILE = ROOT / "data" / "customers.csv"
PORT = int(os.environ.get("PORT", "8000"))

def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con

def init_db():
    con=connect()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS customer_source(
      customer_id TEXT PRIMARY KEY, name TEXT NOT NULL, age INTEGER NOT NULL,
      annual_income REAL, region TEXT NOT NULL, channel TEXT NOT NULL,
      membership TEXT NOT NULL, tenure_years INTEGER NOT NULL,
      spending_score REAL NOT NULL, annual_spend REAL NOT NULL,
      spending_behavior TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS dim_customer(
      customer_key INTEGER PRIMARY KEY AUTOINCREMENT,
      customer_id TEXT UNIQUE NOT NULL, name TEXT NOT NULL, age INTEGER NOT NULL,
      annual_income REAL, tenure_years INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS dim_region(
      region_key INTEGER PRIMARY KEY AUTOINCREMENT, region_name TEXT UNIQUE NOT NULL
    );
    CREATE TABLE IF NOT EXISTS dim_channel(
      channel_key INTEGER PRIMARY KEY AUTOINCREMENT, channel_name TEXT UNIQUE NOT NULL
    );
    CREATE TABLE IF NOT EXISTS dim_membership(
      membership_key INTEGER PRIMARY KEY AUTOINCREMENT, membership_name TEXT UNIQUE NOT NULL
    );
    CREATE TABLE IF NOT EXISTS dim_date(
      date_key INTEGER PRIMARY KEY, full_date TEXT NOT NULL, year INTEGER NOT NULL, month INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS fact_customer_spending(
      fact_key INTEGER PRIMARY KEY AUTOINCREMENT,
      customer_key INTEGER NOT NULL REFERENCES dim_customer(customer_key),
      region_key INTEGER NOT NULL REFERENCES dim_region(region_key),
      channel_key INTEGER NOT NULL REFERENCES dim_channel(channel_key),
      membership_key INTEGER NOT NULL REFERENCES dim_membership(membership_key),
      date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
      spending_score REAL NOT NULL, annual_spend REAL NOT NULL,
      spending_behavior TEXT NOT NULL,
      UNIQUE(customer_key,date_key)
    );
    """)
    con.commit()
    con.close()

def seed_source():
    con=connect()
    count=con.execute("SELECT COUNT(*) n FROM customer_source").fetchone()["n"]
    if count==0 and CSV_FILE.exists():
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                con.execute("""INSERT OR IGNORE INTO customer_source VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                  (r["customer_id"],r["name"],int(r["age"]),float(r["annual_income"]),
                   r["region"],r["channel"],r["membership"],int(r["tenure_years"]),
                   float(r["spending_score"]),float(r["annual_spend"]),r["spending_behavior"]))
    con.commit(); con.close()

def refresh_star():
    con=connect()
    today=date.today()
    dk=int(today.strftime("%Y%m%d"))
    con.execute("INSERT OR IGNORE INTO dim_date VALUES (?,?,?,?)",
                (dk,today.isoformat(),today.year,today.month))
    src=con.execute("SELECT * FROM customer_source").fetchall()
    for s in src:
        con.execute("INSERT OR IGNORE INTO dim_customer(customer_id,name,age,annual_income,tenure_years) VALUES (?,?,?,?,?)",
                    (s["customer_id"],s["name"],s["age"],s["annual_income"],s["tenure_years"]))
        con.execute("INSERT OR IGNORE INTO dim_region(region_name) VALUES (?)",(s["region"],))
        con.execute("INSERT OR IGNORE INTO dim_channel(channel_name) VALUES (?)",(s["channel"],))
        con.execute("INSERT OR IGNORE INTO dim_membership(membership_name) VALUES (?)",(s["membership"],))
        ck=con.execute("SELECT customer_key FROM dim_customer WHERE customer_id=?",(s["customer_id"],)).fetchone()[0]
        rk=con.execute("SELECT region_key FROM dim_region WHERE region_name=?",(s["region"],)).fetchone()[0]
        hk=con.execute("SELECT channel_key FROM dim_channel WHERE channel_name=?",(s["channel"],)).fetchone()[0]
        mk=con.execute("SELECT membership_key FROM dim_membership WHERE membership_name=?",(s["membership"],)).fetchone()[0]
        con.execute("""INSERT OR REPLACE INTO fact_customer_spending
          (customer_key,region_key,channel_key,membership_key,date_key,spending_score,annual_spend,spending_behavior)
          VALUES (?,?,?,?,?,?,?,?)""",
          (ck,rk,hk,mk,dk,s["spending_score"],s["annual_spend"],s["spending_behavior"]))
    con.commit(); con.close()
    return len(src)

def query_dashboard(region="All", tier="All"):
    con=connect()
    where=[]; args=[]
    if region!="All": where.append("r.region_name=?"); args.append(region)
    if tier!="All": where.append("m.membership_name=?"); args.append(tier)
    clause=(" WHERE "+" AND ".join(where)) if where else ""
    baseq=""" FROM fact_customer_spending f
      JOIN dim_customer c ON f.customer_key=c.customer_key
      JOIN dim_region r ON f.region_key=r.region_key
      JOIN dim_channel h ON f.channel_key=h.channel_key
      JOIN dim_membership m ON f.membership_key=m.membership_key
      JOIN dim_date d ON f.date_key=d.date_key """
    k=con.execute("SELECT COUNT(*) n, COALESCE(AVG(f.annual_spend),0) avg_spend, COALESCE(AVG(f.spending_score),0) avg_score "+baseq+clause,args).fetchone()
    byreg=con.execute("SELECT r.region_name label, ROUND(AVG(f.annual_spend),2) value "+baseq+clause+" GROUP BY r.region_name ORDER BY value DESC",args).fetchall()
    bytier=con.execute("SELECT m.membership_name label, ROUND(AVG(f.annual_spend),2) value "+baseq+clause+" GROUP BY m.membership_name ORDER BY value DESC",args).fetchall()
    data=con.execute("SELECT c.customer_id,c.name,c.age,c.annual_income,r.region_name region,h.channel_name channel,m.membership_name membership,c.tenure_years,f.spending_score,f.annual_spend,f.spending_behavior "+baseq+clause+" ORDER BY f.annual_spend DESC",args).fetchall()
    regions=[x[0] for x in con.execute("SELECT region_name FROM dim_region ORDER BY region_name").fetchall()]
    tiers=[x[0] for x in con.execute("SELECT membership_name FROM dim_membership ORDER BY membership_name").fetchall()]
    con.close()
    return k,byreg,bytier,data,regions,tiers

def page(region="All", tier="All", notice=""):
    k,byreg,bytier,data,regions,tiers=query_dashboard(region,tier)
    esc=html.escape
    def opts(values,selected):
        return "".join(f'<option value="{esc(v)}" {"selected" if v==selected else ""}>{esc(v)}</option>' for v in values)
    maxreg=max([x["value"] for x in byreg] or [1]) or 1
    maxtr=max([x["value"] for x in bytier] or [1]) or 1
    regbars="".join(f'<div class="bar"><span>{esc(x["label"])}</span><div class="track"><i style="width:{100*x["value"]/maxreg:.1f}%"></i></div><b>${x["value"]:,.0f}</b></div>' for x in byreg)
    tierbars="".join(f'<div class="bar"><span>{esc(x["label"])}</span><div class="track"><i style="width:{100*x["value"]/maxtr:.1f}%"></i></div><b>${x["value"]:,.0f}</b></div>' for x in bytier)
    trs="".join("<tr>"+"".join(f"<td>{esc(str(x[col]))}</td>" for col in ["customer_id","name","region","channel","membership","annual_income","spending_score","annual_spend","spending_behavior"])+"</tr>" for x in data)
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Customer Analytics</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f2f5f8;color:#263238;font-family:Arial,sans-serif}}
header{{background:#203746;color:white;padding:22px 4%}}header h1{{margin:0 0 7px}}header p{{margin:0;color:#d5e2e9}}
main{{max-width:1250px;margin:auto;padding:24px}}.filters,.cards,.twocol{{display:grid;gap:16px}}.filters{{grid-template-columns:1fr 1fr auto;background:white;padding:16px;border-radius:10px;align-items:end}}
label{{font-size:13px;color:#546e7a}}select,input{{display:block;width:100%;padding:10px;margin-top:6px;border:1px solid #cfd8dc;border-radius:6px;background:white}}
button{{padding:11px 18px;background:#1565c0;color:white;border:0;border-radius:6px;cursor:pointer;font-weight:bold}}.secondary{{background:#455a64}}
.cards{{grid-template-columns:repeat(4,1fr);margin:18px 0}}.card,.panel{{background:white;padding:18px;border-radius:10px;box-shadow:0 2px 8px #0000000c}}.card small{{color:#607d8b}}.val{{font-size:27px;font-weight:bold;margin-top:8px}}.twocol{{grid-template-columns:1fr 1fr}}.bar{{display:grid;grid-template-columns:100px 1fr 75px;gap:10px;align-items:center;margin:15px 0;font-size:13px}}.track{{height:18px;background:#eceff1;border-radius:4px;overflow:hidden}}.track i{{display:block;height:100%;background:#00897b;border-radius:4px}}
.tablewrap{{overflow:auto;max-height:440px}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{padding:10px;border-bottom:1px solid #eceff1;text-align:left;white-space:nowrap}}th{{position:sticky;top:0;background:#eaf0f4}}.notice{{color:#2e7d32;font-weight:bold;margin:12px 0}}.flow{{text-align:center;line-height:2;padding:15px;background:#eaf3f7;border-radius:9px;margin:18px 0}}.foot{{color:#607d8b;font-size:12px;margin:16px 0}}
@media(max-width:800px){{.cards{{grid-template-columns:1fr 1fr}}.twocol,.filters{{grid-template-columns:1fr}}}}
</style></head><body><header><h1>Customer Analytics System</h1><p>Relational Source → Star Schema → Application Dashboard & Reports</p></header>
<main>
<div class="flow"><b>Customer Source</b> &nbsp; → &nbsp; <b>ETL / Refresh</b> &nbsp; → &nbsp; <b>Star Schema</b> &nbsp; → &nbsp; <b>Analytics Application</b></div>
{f'<div class="notice">{esc(notice)}</div>' if notice else ''}
<form class="filters" method="get" action="/"><div><label>Region</label><select name="region"><option>All</option>{opts(regions,region)}</select></div>
<div><label>Membership</label><select name="tier"><option>All</option>{opts(tiers,tier)}</select></div><button type="submit">Apply Filters</button></form>
<div class="cards"><div class="card"><small>Customers in view</small><div class="val">{k["n"]}</div></div>
<div class="card"><small>Average annual spend</small><div class="val">${k["avg_spend"]:,.2f}</div></div>
<div class="card"><small>Average spending score</small><div class="val">{k["avg_score"]:.1f}</div></div>
<div class="card"><small>Star fact records</small><div class="val">{k["n"]}</div></div></div>
<div class="twocol"><section class="panel"><h2>Average spend by region</h2>{regbars or "No data"}</section>
<section class="panel"><h2>Average spend by membership</h2>{tierbars or "No data"}</section></div>
<section class="panel" style="margin-top:18px"><h2>Customer detail report</h2><div class="tablewrap"><table><thead><tr><th>ID</th><th>Name</th><th>Region</th><th>Channel</th><th>Tier</th><th>Income</th><th>Score</th><th>Annual spend</th><th>Behavior</th></tr></thead><tbody>{trs}</tbody></table></div>
<p><a href="/report.csv?region={region}&tier={tier}">Download filtered CSV report</a></p></section>
<div class="twocol" style="margin-top:18px"><section class="panel"><h2>Refresh star schema</h2><p>Reload source CSV records into the source table and rebuild current fact rows.</p><form method="post" action="/refresh"><button class="secondary">Run ETL / Refresh</button></form></section>
<section class="panel"><h2>Add customer</h2><form method="post" action="/add">
<label>Customer ID</label><input name="customer_id" placeholder="C0041" required>
<label>Name</label><input name="name" placeholder="Customer name" required>
<label>Age</label><input name="age" type="number" min="18" max="100" required>
<label>Annual income</label><input name="annual_income" type="number" min="0" required>
<label>Region</label><select name="region"><option>North</option><option>South</option><option>East</option><option>West</option></select>
<label>Channel</label><select name="channel"><option>Online</option><option>Store</option><option>Mobile</option></select>
<label>Membership</label><select name="membership"><option>Basic</option><option>Silver</option><option>Gold</option><option>Platinum</option></select>
<label>Tenure (years)</label><input name="tenure_years" type="number" min="0" max="60" value="1" required>
<label>Spending score (1–100)</label><input name="spending_score" type="number" min="1" max="100" value="50" required>
<label>Annual spend</label><input name="annual_spend" type="number" min="0" value="500" required>
<button style="margin-top:12px">Save customer + refresh</button></form></section></div>
<p class="foot">Teaching demo using synthetic data and a local SQLite database. No external services required. For SQL Server deployment, see docs/SQLSERVER_DEPLOYMENT.md.</p>
</main></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def send(self, body, ctype="text/html; charset=utf-8", status=200):
        raw=body.encode("utf-8")
        self.send_response(status); self.send_header("Content-Type",ctype)
        self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        u=urlparse(self.path)
        q=parse_qs(u.query)
        region=q.get("region",["All"])[0]; tier=q.get("tier",["All"])[0]
        if u.path=="/":
            self.send(page(region,tier)); return
        if u.path=="/report.csv":
            _,_,_,data,_,_=query_dashboard(region,tier)
            import io
            out=io.StringIO(); w=csv.writer(out)
            w.writerow(["customer_id","name","age","annual_income","region","channel","membership","tenure_years","spending_score","annual_spend","spending_behavior"])
            for r in data:
                w.writerow([r["customer_id"],r["name"],r["age"],r["annual_income"],r["region"],r["channel"],r["membership"],r["tenure_years"],r["spending_score"],r["annual_spend"],r["spending_behavior"]])
            self.send(out.getvalue(),"text/csv; charset=utf-8"); return
        self.send("Not found",status=404)
    def do_POST(self):
        length=int(self.headers.get("Content-Length",0))
        form=parse_qs(self.rfile.read(length).decode("utf-8"))
        if self.path=="/refresh":
            n=refresh_star()
            self.send(page(notice=f"Star schema refreshed from {n} source customer records.")); return
        if self.path=="/add":
            try:
                get=lambda k: form[k][0].strip()
                sid=get("customer_id"); name=get("name"); age=int(get("age")); income=float(get("annual_income"))
                region=get("region"); channel=get("channel"); membership=get("membership")
                tenure=int(get("tenure_years")); score=float(get("spending_score")); spend=float(get("annual_spend"))
                if not sid or not name or not (1<=score<=100) or min(age,income,tenure,spend)<0: raise ValueError("Invalid field value")
                behavior="High" if score>=70 else ("Medium" if score>=40 else "Low")
                con=connect()
                con.execute("INSERT INTO customer_source VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  (sid,name,age,income,region,channel,membership,tenure,score,spend,behavior))
                con.commit(); con.close()
                n=refresh_star()
                self.send(page(notice=f"Customer {sid} saved. Star schema refreshed ({n} customers).")); return
            except sqlite3.IntegrityError:
                self.send(page(notice="Customer ID already exists. Use a unique ID."),status=400); return
            except Exception as e:
                self.send(page(notice=f"Could not save customer: {e}"),status=400); return
        self.send("Not found",status=404)
    def log_message(self, fmt, *args):
        print(fmt % args)

if __name__=="__main__":
    init_db(); seed_source(); n=refresh_star()
    print(f"Initialized {DB} with {n} customers")
    print(f"Open http://127.0.0.1:{PORT}")
    HTTPServer(("127.0.0.1",PORT),Handler).serve_forever()
