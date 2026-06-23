import re,json,os,asyncio,traceback,sys,random
from datetime import datetime,timedelta
from playwright.async_api import async_playwright

DATA_FILE=os.path.join(os.path.dirname(__file__),"..","docs","data","reviews.json")
BACKUP_DIR=os.path.join(os.path.dirname(DATA_FILE),"backups")
MAX_CONCURRENT=4
IST=timedelta(hours=5,minutes=30)

BRANCHES=[
    # Sivaperumal
    {"id":1,"name":"Tuticorin-1","place_id":"ChIJ5zJNoJfvAzsR-bJE_3bbNYw","agm":"Sivaperumal"},
    {"id":2,"name":"Tuticorin-2","place_id":"ChIJH6gY4-PvAzsRJ50skTlx3cs","agm":"Sivaperumal"},
    {"id":3,"name":"Thiruchendur-1","place_id":"ChIJeXA4vJKRAzsRBovAtv6lMuQ","agm":"Sivaperumal"},
    {"id":4,"name":"Thisayanvilai-1","place_id":"ChIJVWkvdfh_BDsRdvtimKCLS5Y","agm":"Sivaperumal"},
    {"id":5,"name":"Eral-2","place_id":"ChIJbwAA0KGMAzsRkQilW5PceeA","agm":"Sivaperumal"},
    {"id":6,"name":"Udankudi","place_id":"ChIJPQAAACyEAzsRgjznQ1GLom0","agm":"Sivaperumal"},
    # Johnson
    {"id":7,"name":"Tirunelveli-1","place_id":"ChIJ2RU2NvQRBDsRq-Fw7IVwx7k","agm":"Johnson"},
    {"id":8,"name":"Valliyur-1","place_id":"ChIJcVNk6TtnBDsRBoP4zpExt5k","agm":"Johnson"},
    {"id":9,"name":"Ambasamudram-1","place_id":"ChIJ9SGeIi85BDsRZk4QdyW9BSY","agm":"Johnson"},
    {"id":10,"name":"Anjugramam-1","place_id":"ChIJ4yeJebLtBDsRDceoxujdGyc","agm":"Johnson"},
    # Muthuselvam
    {"id":11,"name":"Thenkasi","place_id":"ChIJuaqqquEpBDsRVITw0MMYklc","agm":"Muthuselvam"},
    {"id":12,"name":"Thenkasi-2","place_id":"ChIJiwqLye6DBjsRo9v1mWXaycI","agm":"Muthuselvam"},
    {"id":13,"name":"Surandai-1","place_id":"ChIJPb1_eEOdBjsRjL9IVCVJhi8","agm":"Muthuselvam"},
    {"id":14,"name":"Puliyankudi-1","place_id":"ChIJjZqoc46RBjsRQTGHnNC8xxA","agm":"Muthuselvam"},
    {"id":15,"name":"Sengottai-1","place_id":"ChIJw3zzKiaBBjsR9KDyGpn1nXU","agm":"Muthuselvam"},
    {"id":16,"name":"Rajapalayam","place_id":"ChIJW2ot-NDpBjsRMTfMF2IV-xE","agm":"Muthuselvam"},
    # Jeeva
    {"id":17,"name":"Nagercoil","place_id":"ChIJe1LZBiTxBDsRJFLjlbgZoIs","agm":"Jeeva"},
    {"id":18,"name":"Marthandam","place_id":"ChIJcWptCRdVBDsRlJh2q0-rnfY","agm":"Jeeva"},
    {"id":19,"name":"Thuckalay-1","place_id":"ChIJc9QgEub4BDsRoyDR4Wd6tYA","agm":"Jeeva"},
    {"id":20,"name":"Colachel-1","place_id":"ChIJgRkBLw39BDsR58D0lwNo5Ts","agm":"Jeeva"},
    {"id":21,"name":"Kulasekharam-1","place_id":"ChIJw0Ep-kNXBDsRe5ad32jAeAk","agm":"Jeeva"},
    {"id":22,"name":"Monday Market","place_id":"ChIJTceRGAD5BDsR65i3YNTcYHk","agm":"Jeeva"},
    {"id":23,"name":"Karungal-1","place_id":"ChIJfTP5ASr_BDsRgsBaeQltkw4","agm":"Jeeva"},
    # Seenivasan
    {"id":24,"name":"Kovilpatti","place_id":"ChIJHY0o-26yBjsRt7wbXB1pDUE","agm":"Seenivasan"},
    {"id":25,"name":"Kayathar-1","place_id":"ChIJx5ebtUgRBDsRMquPZNUJVpw","agm":"Seenivasan"},
    {"id":26,"name":"Ramnad","place_id":"ChIJNVVVVaGiATsRnunSgOTvbE8","agm":"Seenivasan"},
    {"id":27,"name":"Paramakudi","place_id":"ChIJ-dgjBzQHATsRf27FWAJgmsA","agm":"Seenivasan"},
    {"id":28,"name":"Sayalkudi-1","place_id":"ChIJRTqudn9lATsR2fYyMmxlOrw","agm":"Seenivasan"},
    {"id":29,"name":"Sattur-2","place_id":"ChIJNVVVVcHKBjsR7xMX97RFn8Q","agm":"Seenivasan"},
    {"id":30,"name":"Sankarankovil-1","place_id":"ChIJE1mKnhSXBjsRKMQ-9JKQf_c","agm":"Seenivasan"},
    {"id":31,"name":"Villathikullam","place_id":"ChIJi_wAkwVbATsRtFl3_V5rGrY","agm":"Seenivasan"},
    # Venkadesan
    {"id":32,"name":"Virudhunagar","place_id":"ChIJN3jzNJgsATsRCU3nrB5ntKE","agm":"Venkadesan"},
    {"id":33,"name":"Virudhunagar-2","place_id":"ChIJPezaX7wtATsR9sHhFOG6A1c","agm":"Venkadesan"},
    {"id":34,"name":"Aruppukottai","place_id":"ChIJy6qqqgYwATsRbcp-hXnoruM","agm":"Venkadesan"},
    {"id":35,"name":"Aruppukottai-2","place_id":"ChIJY04wY58xATsRuoJSichVQQE","agm":"Venkadesan"},
    {"id":36,"name":"Sivakasi","place_id":"ChIJI2JvEePOBjsREh8b-x4WF4U","agm":"Venkadesan"},
]

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE,"r",encoding="utf-8") as f:
                d=json.load(f)
            if d.get("branches"): return d
        except: pass
    if os.path.exists(BACKUP_DIR):
        for bf in sorted(os.listdir(BACKUP_DIR),reverse=True):
            if not bf.endswith(".json"): continue
            try:
                with open(os.path.join(BACKUP_DIR,bf),"r",encoding="utf-8") as f:
                    d=json.load(f)
                if d.get("branches"): return d
            except: continue
    return {"branches":{},"daily":{},"logs":[]}

def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE),exist_ok=True)
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=2,ensure_ascii=False)
    os.makedirs(BACKUP_DIR,exist_ok=True)
    snap=(datetime.utcnow()+IST).strftime("%Y-%m-%d")
    bp=os.path.join(BACKUP_DIR,f"reviews_{snap}.json")
    with open(bp,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=2,ensure_ascii=False)
    for fn in os.listdir(BACKUP_DIR):
        fp=os.path.join(BACKUP_DIR,fn)
        try:
            if (datetime.utcnow()-datetime.fromtimestamp(os.path.getmtime(fp))).days>90:
                os.remove(fp)
        except: pass

def resolve_date(rel,snap_date):
    if not rel: return ""
    r=rel.lower().strip()
    snap=datetime.strptime(snap_date,"%Y-%m-%d").date()
    if any(x in r for x in ["just now","second","minute","moment"]): return str(snap)
    if "hour" in r:
        m=re.search(r"(\d+)",r); h=int(m.group(1)) if m else 1
        return str(snap) if h<=23 else str(snap-timedelta(days=1))
    if "1 day" in r or "a day" in r or "yesterday" in r: return str(snap-timedelta(days=1))
    if "day" in r:
        m=re.search(r"(\d+)",r)
        return str(snap-timedelta(days=int(m.group(1)) if m else 1))
    if "week" in r:
        m=re.search(r"(\d+)",r)
        return str(snap-timedelta(weeks=int(m.group(1)) if m else 1))
    if "month" in r:
        m=re.search(r"(\d+)",r)
        return str(snap-timedelta(days=30*(int(m.group(1)) if m else 1)))
    for fmt in ["%b %d, %Y","%d %B %Y","%B %d, %Y","%d %b %Y","%Y-%m-%d"]:
        try: return datetime.strptime(rel.strip(),fmt).strftime("%Y-%m-%d")
        except: pass
    return ""

async def get_overall_rating(page):
    count,stars=None,None
    content=await page.content()
    for sel in ['[aria-label*="reviews"]','[aria-label*="Reviews"]']:
        for el in await page.locator(sel).all():
            lb=await el.get_attribute("aria-label") or ""
            m=re.search(r"([\d,]+)",lb)
            if m:
                v=int(m.group(1).replace(",",""))
                if v>10: count=v; break
        if count: break
    if not count:
        for pat in [r'([\d,]+)\s*reviews?',r'"reviewCount"["\s:]+(\d+)']:
            m=re.search(pat,content,re.IGNORECASE)
            if m:
                v=int(m.group(1).replace(",",""))
                if v>10: count=v; break
    for sel in ['[aria-label*="stars"]','[aria-label*="star rating"]']:
        for el in await page.locator(sel).all():
            lb=await el.get_attribute("aria-label") or ""
            m=re.search(r"(\d\.\d)",lb)
            if m: stars=float(m.group(1)); break
        if stars: break
    if not stars:
        for pat in [r'"ratingValue":"([\d.]+)"',r'(\d\.\d)\s*(?:stars|out of 5)']:
            m=re.search(pat,content,re.IGNORECASE)
            if m:
                try:
                    v=float(m.group(1))
                    if 1.0<=v<=5.0: stars=v; break
                except: pass
    return count,stars

async def scroll_count(page,snap_date):
    """Count reviews dated snap_date by scrolling Newest sort. snap_date=yesterday."""
    for sel in ['button[aria-label="Reviews"]','button[data-tab-index="1"]']:
        try:
            t=await page.wait_for_selector(sel,timeout=4000)
            if t: await t.click(); await page.wait_for_timeout(1500); break
        except: continue
    for sel in ['button[aria-label="Sort reviews"]','button[data-value="Sort"]']:
        try:
            sb=await page.wait_for_selector(sel,timeout=4000)
            if sb:
                await sb.click(); await page.wait_for_timeout(800)
                for ns in ['li[data-index="1"]','li:has-text("Newest")','div[role="menuitemradio"]:has-text("Newest")']:
                    try:
                        n=await page.wait_for_selector(ns,timeout=2000)
                        if n: await n.click(); await page.wait_for_timeout(1500); break
                    except: continue
                break
        except: continue
    seen,count,stop,nono=set(),0,False,0
    while not stop and nono<5:
        cards=await page.query_selector_all('div[data-review-id],div.jftiEf')
        new=0
        for card in cards:
            rid=await card.get_attribute("data-review-id") or str(id(card))
            if rid in seen: continue
            seen.add(rid); new+=1
            ds=""
            for dsel in ['span.rsqaWe','span[class*="DU9Pgb"]','span[class*="xRkPPb"]']:
                de=await card.query_selector(dsel)
                if de: ds=(await de.inner_text()).strip(); break
            resolved=resolve_date(ds,snap_date)
            if resolved==snap_date: count+=1
            elif resolved and resolved<snap_date: stop=True; break
        nono=0 if new else nono+1
        if not stop:
            try:
                pane=await page.query_selector('div.m6QErb[tabindex="-1"],div.m6QErb')
                if pane: await pane.evaluate("el=>el.scrollBy(0,2000)")
                else: await page.keyboard.press("End")
            except: pass
            await page.wait_for_timeout(random.randint(600,1200))
    return count

async def scrape_branch(ctx,branch,snap_date,prev_total,old_stars):
    res={"live":None,"stars":None,"daily":0,"method":"scroll","error":None}
    page=None
    try:
        page=await ctx.new_page()
        await page.goto(f"https://www.google.com/maps/place/?q=place_id:{branch['place_id']}",
                        wait_until="domcontentloaded",timeout=35000)
        await page.wait_for_timeout(random.randint(2500,4000))
        live,stars=await get_overall_rating(page)
        res["live"]=live; res["stars"]=stars or old_stars
        if not live: res["error"]="no count"; return res
        # Primary: scroll count
        try:
            res["daily"]=await scroll_count(page,snap_date)
            res["method"]="scroll"
            print(f"  ✓ {branch['name']}: overall={live} snap={res['daily']} ★{res['stars']} (scroll)")
        except Exception as se:
            # Fallback: snapshot diff
            raw=live-prev_total if prev_total else 0
            res["daily"]=max(0,raw); res["method"]="diff"
            print(f"  ! {branch['name']}: scroll failed ({se}), diff={res['daily']}")
    except Exception as e:
        res["error"]=str(e); print(f"  ✗ {branch['name']}: {e}")
    finally:
        if page:
            try: await page.close()
            except: pass
    return res

async def run():
    now_ist=datetime.utcnow()+IST
    # Scraper runs at 11:50 PM IST → snap_date = TODAY
    snap_date=now_ist.date().strftime("%Y-%m-%d")
    run_time=datetime.utcnow().isoformat()
    print(f"=== Scraper === snap={snap_date} ({now_ist.strftime('%H:%M IST')})")

    data=load_data()
    prev_dates=sorted([d for d in data.get("daily",{}) if d<snap_date],reverse=True)
    baseline_date=prev_dates[0] if prev_dates else None
    baseline_snap=data["daily"].get(baseline_date,{}) if baseline_date else {}
    if snap_date not in data["daily"]: data["daily"][snap_date]={}

    snap_month=snap_date[:7]
    prev_month=sorted([d for d in data.get("daily",{}) if d.startswith(snap_month) and d<snap_date])
    monthly_snap=data["daily"].get(prev_month[-1],{}) if prev_month else {}

    results={};success=0;failed=[]

    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=[
            "--no-sandbox","--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled","--disable-gpu"])
        ctx=await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            locale="en-IN",viewport={"width":1280,"height":800})
        try:
            wp=await ctx.new_page()
            await wp.goto("https://www.google.com/maps",wait_until="domcontentloaded",timeout=20000)
            await wp.wait_for_timeout(1500); await wp.close()
        except: pass

        sem=asyncio.Semaphore(MAX_CONCURRENT)
        async def bounded(branch):
            nonlocal success
            async with sem:
                bid=str(branch["id"])
                prev=baseline_snap.get(bid,{}).get("total_snap",
                     data.get("branches",{}).get(bid,{}).get("overall",0))
                old_s=data.get("branches",{}).get(bid,{}).get("star_rating",0)
                print(f"[{branch['id']:02}/36] {branch['name']}")
                res=await scrape_branch(ctx,branch,snap_date,prev,old_s)
                if res["error"]: failed.append(branch["name"])
                else: results[bid]=res; success+=1
                await asyncio.sleep(0.5)

        await asyncio.gather(*[bounded(b) for b in BRANCHES])
        await browser.close()

    for b in BRANCHES:
        bid=str(b["id"])
        if bid not in results: continue
        r=results[bid]
        prev_m=monthly_snap.get(bid,{}).get("monthly",0)
        monthly=prev_m+r["daily"]
        raw_delta=r["live"]-baseline_snap.get(bid,{}).get("total_snap",
                  data.get("branches",{}).get(bid,{}).get("overall",0))
        data["daily"][snap_date][bid]={
            "total_snap":r["live"],"daily_count":r["daily"],
            "raw_delta":raw_delta,"has_deletion":raw_delta<0,
            "monthly":monthly,"star_rating":r["stars"] or 0,"method":r["method"]
        }
        data["branches"][bid]={
            "id":b["id"],"name":b["name"],"agm":b["agm"],
            "overall":r["live"],"star_rating":r["stars"] or 0,"monthly":monthly
        }

    data.setdefault("logs",[]).insert(0,{
        "ran_at":run_time,"snap_date":snap_date,"baseline_date":baseline_date,
        "success":success,"failed":len(failed),"failed_names":failed
    })
    data["logs"]=data["logs"][:50]
    data["last_updated"]=run_time
    save_data(data)
    print(f"=== Done {success}/36 for {snap_date} ===")

if __name__=="__main__":
    try: asyncio.run(run())
    except Exception as e:
        print(f"FATAL: {e}"); traceback.print_exc(); sys.exit(1)
