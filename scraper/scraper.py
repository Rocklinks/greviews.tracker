#!/usr/bin/env python3
"""
Google Reviews Scraper — Playwright only.
Scrapes total review count, star rating, and yesterday's reviews for 36 branches.
Runs at ~1 PM IST → collects reviews posted on the previous calendar day (IST).
"""

import asyncio, traceback, sys, os, json, re, time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────
IST = timedelta(hours=5, minutes=30)
DATA_FILE = Path(__file__).parent / "reviews.json"
BACKUP_DIR = Path(__file__).parent / "backups"
MIN_SUCCESS = 10
CONCURRENCY = 3   # keep low — Google blocks aggressive parallel scraping

BRANCHES = [
    {"id": 1,  "name": "Tuticorin-1",      "place_id": "ChIJ5zJNoJfvAzsR-bJE_3bbNYw", "agm": "Sivaperumal"},
    {"id": 2,  "name": "Tuticorin-2",      "place_id": "ChIJH6gY4-PvAzsRJ50skTlx3cs", "agm": "Sivaperumal"},
    {"id": 3,  "name": "Thiruchendur-1",   "place_id": "ChIJeXA4vJKRAzsRBovAtv6lMuQ", "agm": "Sivaperumal"},
    {"id": 4,  "name": "Thisayanvilai-1",  "place_id": "ChIJVWkvdfh_BDsRdvtimKCLS5Y", "agm": "Sivaperumal"},
    {"id": 5,  "name": "Eral-2",           "place_id": "ChIJbwAA0KGMAzsRkQilW5PceeA", "agm": "Sivaperumal"},
    {"id": 6,  "name": "Udankudi",         "place_id": "ChIJPQAAACyEAzsRgjznQ1GLom0", "agm": "Sivaperumal"},
    {"id": 7,  "name": "Tirunelveli-1",    "place_id": "ChIJ2RU2NvQRBDsRq-Fw7IVwx7k", "agm": "Johnson"},
    {"id": 8,  "name": "Valliyur-1",       "place_id": "ChIJcVNk6TtnBDsRBoP4zpExt5k", "agm": "Johnson"},
    {"id": 9,  "name": "Ambasamudram-1",   "place_id": "ChIJ9SGeIi85BDsRZk4QdyW9BSY", "agm": "Johnson"},
    {"id": 10, "name": "Anjugramam-1",     "place_id": "ChIJ4yeJebLtBDsRDceoxujdGyc", "agm": "Johnson"},
    {"id": 11, "name": "Nagercoil",        "place_id": "ChIJe1LZBiTxBDsRJFLjlbgZoIs", "agm": "Jeeva"},
    {"id": 12, "name": "Marthandam",       "place_id": "ChIJcWptCRdVBDsRlJh2q0-rnfY", "agm": "Jeeva"},
    {"id": 13, "name": "Thuckalay-1",      "place_id": "ChIJc9QgEub4BDsRoyDR4Wd6tYA", "agm": "Jeeva"},
    {"id": 14, "name": "Colachel-1",       "place_id": "ChIJgRkBLw39BDsR58D0lwNo5Ts", "agm": "Jeeva"},
    {"id": 15, "name": "Kulasekharam-1",   "place_id": "ChIJw0Ep-kNXBDsRe5ad32jAeAk", "agm": "Jeeva"},
    {"id": 16, "name": "Monday Market",    "place_id": "ChIJTceRGAD5BDsR65i3YNTcYHk", "agm": "Jeeva"},
    {"id": 17, "name": "Karungal-1",       "place_id": "ChIJfTP5ASr_BDsRgsBaeQltkw4", "agm": "Jeeva"},
    {"id": 18, "name": "Kovilpatti",       "place_id": "ChIJHY0o-26yBjsRt7wbXB1pDUE", "agm": "Seenivasan"},
    {"id": 19, "name": "Ramnad",           "place_id": "ChIJNVVVVaGiATsRnunSgOTvbE8", "agm": "Seenivasan"},
    {"id": 20, "name": "Paramakudi",       "place_id": "ChIJ-dgjBzQHATsRf27FWAJgmsA", "agm": "Seenivasan"},
    {"id": 21, "name": "Sayalkudi-1",      "place_id": "ChIJRTqudn9lATsR2fYyMmxlOrw", "agm": "Seenivasan"},
    {"id": 22, "name": "Villathikullam",   "place_id": "ChIJi_wAkwVbATsRtFl3_V5rGrY", "agm": "Seenivasan"},
    {"id": 23, "name": "Sattur-2",         "place_id": "ChIJNVVVVcHKBjsR7xMX97RFn8Q", "agm": "Seenivasan"},
    {"id": 24, "name": "Sankarankovil-1",  "place_id": "ChIJE1mKnhSXBjsRKMQ-9JKQf_c", "agm": "Seenivasan"},
    {"id": 25, "name": "Kayathar-1",       "place_id": "ChIJx5ebtUgRBDsRMquPZNUJVpw", "agm": "Seenivasan"},
    {"id": 26, "name": "Thenkasi",         "place_id": "ChIJuaqqquEpBDsRVITw0MMYklc", "agm": "Muthuselvam"},
    {"id": 27, "name": "Thenkasi-2",       "place_id": "ChIJiwqLye6DBjsRo9v1mWXaycI", "agm": "Muthuselvam"},
    {"id": 28, "name": "Surandai-1",       "place_id": "ChIJPb1_eEOdBjsRjL9IVCVJhi8", "agm": "Muthuselvam"},
    {"id": 29, "name": "Puliyankudi-1",    "place_id": "ChIJjZqoc46RBjsRQTGHnNC8xxA", "agm": "Muthuselvam"},
    {"id": 30, "name": "Sengottai-1",      "place_id": "ChIJw3zzKiaBBjsR9KDyGpn1nXU", "agm": "Muthuselvam"},
    {"id": 31, "name": "Rajapalayam",      "place_id": "ChIJW2ot-DDpBjsRMTfMF2IV-xE", "agm": "Muthuselvam"},
    {"id": 32, "name": "Virudhunagar",     "place_id": "ChIJN3jzNJgsATsRCU3nrB5ntKE", "agm": "Venkadesan"},
    {"id": 33, "name": "Virudhunagar-2",   "place_id": "ChIJPezaX7wtATsR9sHhFOG6A1c", "agm": "Venkadesan"},
    {"id": 34, "name": "Aruppukottai",     "place_id": "ChIJy6qqqgYwATsRbcp-hXnoruM", "agm": "Venkadesan"},
    {"id": 35, "name": "Aruppukottai-2",   "place_id": "ChIJY04wY58xATsRuoJSichVQQE", "agm": "Venkadesan"},
    {"id": 36, "name": "Sivakasi",         "place_id": "ChIJI2JvEePOBjsREh8b-x4WF4U", "agm": "Venkadesan"},
]

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['en-IN', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3]});
window.chrome = { runtime: {} };
"""

# ── Data helpers ─────────────────────────────────────────────────────────────

def load_data() -> dict:
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"branches": {}, "daily": {}, "logs": []}


def save_data(data: dict):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if DATA_FILE.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        import shutil
        shutil.copy2(DATA_FILE, BACKUP_DIR / f"reviews_{ts}.json")
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Date helpers ─────────────────────────────────────────────────────────────

def ist_now() -> datetime:
    return datetime.now(timezone.utc) + IST


def parse_relative_date(text: str, today_ist: datetime) -> str | None:
    """
    Convert Google's relative time strings to YYYY-MM-DD (IST).
    Returns None if can't parse or review is older than yesterday.
    'yesterday' and '1 day ago' → yesterday.
    'a day ago', '2 hours ago', '3 hours ago' etc → yesterday or today depending on hour.
    Anything with 'week', 'month', 'year' → too old, return None.
    """
    t = text.lower().strip()
    yesterday = (today_ist - timedelta(days=1)).date()
    today = today_ist.date()

    if "just now" in t or "minute" in t or "hour" in t:
        # Posted today IST — not yesterday's review
        # But if scraper runs at 1 PM, "hours ago" could be today morning → skip
        return today.strftime("%Y-%m-%d")

    if "yesterday" in t or "1 day ago" in t or "a day ago" in t:
        return yesterday.strftime("%Y-%m-%d")

    if "day" in t:
        m = re.search(r'(\d+)\s*day', t)
        if m:
            days = int(m.group(1))
            d = (today_ist - timedelta(days=days)).date()
            return d.strftime("%Y-%m-%d")

    # week/month/year → too old
    return None


# ── Core scrape function ─────────────────────────────────────────────────────

async def scrape_branch(browser, branch: dict, snap_date: str, yesterday: str) -> dict:
    """
    Scrape one branch. Returns dict with:
      total, stars, reviews (list of yesterday's reviews), error
    """
    url = f"https://www.google.com/maps/place/?q=place_id:{branch['place_id']}"
    result = {
        "total": 0,
        "stars": 0.0,
        "reviews": [],
        "error": None,
    }

    page = None
    try:
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-IN",
            viewport={"width": 1366, "height": 768},
            java_script_enabled=True,
        )
        await ctx.add_init_script(STEALTH_JS)
        page = await ctx.new_page()

        # Block images/fonts to speed up
        await page.route("**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf}", lambda r: r.abort())

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)

        # ── 1. Total review count ────────────────────────────────────────────
        total = 0
        # Try multiple selectors — Google changes these often
        count_selectors = [
            'button[jsaction*="reviewChart"] span',   # "1,234 reviews"
            'span[aria-label*="review"]',
            'div[jsaction*="pane.reviewChart"] span',
            'button span:has-text("review")',
            'span:has-text("reviews")',
        ]
        for sel in count_selectors:
            try:
                els = await page.query_selector_all(sel)
                for el in els:
                    txt = (await el.text_content() or "").strip()
                    m = re.search(r'([\d,]+)\s*review', txt, re.I)
                    if m:
                        total = int(m.group(1).replace(",", ""))
                        break
                if total:
                    break
            except Exception:
                continue

        # Fallback: scan all text on page for "N reviews" pattern
        if not total:
            try:
                body = await page.content()
                m = re.search(r'([\d,]+)\s*review', body, re.I)
                if m:
                    total = int(m.group(1).replace(",", ""))
            except Exception:
                pass

        result["total"] = total

        # ── 2. Star rating ───────────────────────────────────────────────────
        stars = 0.0
        star_selectors = [
            'div[jsaction*="pane.rating"] span[aria-hidden="true"]',
            'span[aria-label*="star"]',
            'div.F7nice span[aria-hidden="true"]',
            'span.ceNzKf',
            'div[jslog*="mutable:true"] span[aria-hidden="true"]',
        ]
        for sel in star_selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    txt = (await el.text_content() or "").strip()
                    m = re.search(r'(\d+\.?\d*)', txt)
                    if m:
                        stars = float(m.group(1))
                        if 1.0 <= stars <= 5.0:
                            break
            except Exception:
                continue

        # Fallback: aria-label on rating div
        if not stars:
            try:
                el = await page.query_selector('[aria-label*="Rated"]')
                if el:
                    lbl = await el.get_attribute("aria-label") or ""
                    m = re.search(r'(\d+\.?\d*)', lbl)
                    if m:
                        stars = float(m.group(1))
            except Exception:
                pass

        result["stars"] = stars

        # ── 3. Navigate to reviews tab ───────────────────────────────────────
        if total > 0:
            try:
                # Click "Reviews" tab
                reviews_tab = await page.query_selector(
                    'button[aria-label*="Review"], button[data-tab-index="1"], '
                    'button:has-text("Reviews")'
                )
                if reviews_tab:
                    await reviews_tab.click()
                    await page.wait_for_timeout(2000)

                # Sort by Newest
                sort_btn = await page.query_selector(
                    'button[aria-label*="Sort"], button[data-value*="sort"], '
                    'button[jsaction*="sort"]'
                )
                if sort_btn:
                    await sort_btn.click()
                    await page.wait_for_timeout(1000)
                    # Click "Newest" option
                    newest = await page.query_selector(
                        'li[data-index="1"], div[data-index="1"], '
                        'li:has-text("Newest"), div:has-text("Newest")'
                    )
                    if newest:
                        await newest.click()
                        await page.wait_for_timeout(2000)

                # ── 4. Scroll & collect yesterday's reviews ──────────────────
                today_ist_dt = ist_now()
                yesterday_str = (today_ist_dt - timedelta(days=1)).date().strftime("%Y-%m-%d")
                reviews_found = []
                seen_ids = set()
                stop_scrolling = False
                scroll_attempts = 0
                max_scrolls = 40

                review_container_sel = (
                    'div[data-review-id], div[jslog*="review"], '
                    'div[class*="jJc9Ad"], div[class*="GHT2ce"]'
                )

                while not stop_scrolling and scroll_attempts < max_scrolls:
                    review_els = await page.query_selector_all(review_container_sel)

                    for rev_el in review_els:
                        try:
                            # Get review ID
                            rev_id = (
                                await rev_el.get_attribute("data-review-id") or
                                await rev_el.get_attribute("data-id") or
                                ""
                            )
                            if not rev_id:
                                # Use inner text hash as fallback ID
                                inner = (await rev_el.text_content() or "")[:80]
                                rev_id = str(hash(inner))

                            if rev_id in seen_ids:
                                continue
                            seen_ids.add(rev_id)

                            # Date text
                            date_el = await rev_el.query_selector(
                                'span[class*="rsqaWe"], span[class*="dehysf"], '
                                'span[class*="xRkPPb"], span[aria-label*="ago"], '
                                'span[data-tooltip]'
                            )
                            date_text = ""
                            if date_el:
                                date_text = (
                                    await date_el.get_attribute("aria-label") or
                                    await date_el.text_content() or
                                    ""
                                ).strip()

                            if not date_text:
                                continue

                            parsed_date = parse_relative_date(date_text, today_ist_dt)

                            # If date is older than yesterday → stop scrolling
                            if parsed_date is None:
                                stop_scrolling = True
                                break
                            if parsed_date < yesterday_str:
                                stop_scrolling = True
                                break

                            # Only keep yesterday's reviews
                            if parsed_date != yesterday_str:
                                continue

                            # Reviewer name
                            name_el = await rev_el.query_selector(
                                'div[class*="d4r55"], button[class*="al6Kxe"], '
                                'span[class*="TSUbDb"], div[class*="e5s1vc"]'
                            )
                            reviewer = (await name_el.text_content() or "Anonymous").strip() if name_el else "Anonymous"

                            # Star rating of review
                            star_el = await rev_el.query_selector(
                                'span[aria-label*="star"], span[role="img"][aria-label]'
                            )
                            rev_stars = 0
                            if star_el:
                                lbl = await star_el.get_attribute("aria-label") or ""
                                m = re.search(r'(\d)', lbl)
                                if m:
                                    rev_stars = int(m.group(1))

                            # Review text — expand if "More" button exists
                            try:
                                more_btn = await rev_el.query_selector(
                                    'button[aria-label="See more"], button[jsaction*="expandReview"]'
                                )
                                if more_btn:
                                    await more_btn.click()
                                    await page.wait_for_timeout(300)
                            except Exception:
                                pass

                            text_el = await rev_el.query_selector(
                                'span[class*="wiI7pd"], div[class*="MyEned"], '
                                'span[jslog*="metadata"]'
                            )
                            rev_text = (await text_el.text_content() or "").strip() if text_el else ""

                            reviews_found.append({
                                "review_id": rev_id,
                                "reviewer": reviewer,
                                "stars": rev_stars,
                                "text": rev_text,
                                "date_text": date_text,
                                "date": parsed_date,
                            })

                        except Exception:
                            continue

                    if stop_scrolling:
                        break

                    # Scroll down inside reviews panel
                    try:
                        scrollable = await page.query_selector(
                            'div[aria-label*="Review"] div[tabindex="-1"], '
                            'div[class*="m6QErb"][class*="DxyBCb"], '
                            'div[jslog*="mutable:true"]'
                        )
                        if scrollable:
                            await scrollable.evaluate("el => el.scrollBy(0, 1200)")
                        else:
                            await page.evaluate("window.scrollBy(0, 1200)")
                    except Exception:
                        await page.evaluate("window.scrollBy(0, 1200)")

                    await page.wait_for_timeout(1200)
                    scroll_attempts += 1

                result["reviews"] = reviews_found

            except Exception as e:
                # Review tab/scroll failed — still keep total+stars
                result["error"] = f"reviews_tab_error: {e}"

        await page.close()
        await ctx.close()

    except Exception as e:
        result["error"] = str(e)
        if page:
            try:
                await page.close()
            except Exception:
                pass

    return result


# ── Orchestrator ─────────────────────────────────────────────────────────────

async def run_all(snap_date: str, yesterday: str) -> tuple[dict, int, list]:
    from playwright.async_api import async_playwright

    results = {}
    success = 0
    failed = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-gpu",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-setuid-sandbox",
                "--ignore-certificate-errors",
            ],
        )

        # Warm up — set cookies so Google sees non-bot traffic
        try:
            ctx = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="en-IN",
            )
            await ctx.add_init_script(STEALTH_JS)
            wp = await ctx.new_page()
            await wp.goto("https://www.google.com", wait_until="domcontentloaded", timeout=15000)
            await wp.wait_for_timeout(2000)
            try:
                accept = await wp.query_selector('button:has-text("Accept all")')
                if accept:
                    await accept.click()
                    await wp.wait_for_timeout(1000)
            except Exception:
                pass
            await wp.close()
            wp2 = await ctx.new_page()
            await wp2.goto("https://www.google.com/maps", wait_until="domcontentloaded", timeout=15000)
            await wp2.wait_for_timeout(2000)
            await wp2.close()
            await ctx.close()
        except Exception:
            pass

        sem = asyncio.Semaphore(CONCURRENCY)

        async def scrape_one(branch):
            nonlocal success
            async with sem:
                bid = str(branch["id"])
                print(f"  [{branch['id']:02}/36] {branch['name']} ...", flush=True)
                res = await scrape_branch(browser, branch, snap_date, yesterday)

                if res["error"] and res["total"] == 0:
                    await asyncio.sleep(3)
                    print(f"  ↻ Retry {branch['name']} ...", flush=True)
                    res = await scrape_branch(browser, branch, snap_date, yesterday)

                if res["total"] == 0 and res["error"]:
                    print(f"  ✗ {branch['name']}: {res['error']}", flush=True)
                    failed.append(branch["name"])
                else:
                    results[bid] = res
                    success += 1
                    rev_count = len(res["reviews"])
                    print(
                        f"  ✓ {branch['name']}: total={res['total']} "
                        f"stars={res['stars']} yesterday_reviews={rev_count}",
                        flush=True,
                    )
                await asyncio.sleep(1)

        await asyncio.gather(*[scrape_one(b) for b in BRANCHES])
        await browser.close()

    return results, success, failed


# ── Save results ─────────────────────────────────────────────────────────────

def save_results(results: dict, success: int, failed: list, snap_date: str, yesterday: str, run_time: str):
    data = load_data()

    # Previous day baseline for delta calc
    prev_dates = sorted([d for d in data.get("daily", {}) if d < snap_date], reverse=True)
    baseline_date = prev_dates[0] if prev_dates else None
    baseline_snap = data["daily"].get(baseline_date, {}) if baseline_date else {}

    data.setdefault("daily", {}).setdefault(snap_date, {})

    # Monthly baseline
    snap_month = snap_date[:7]
    prev_month_dates = sorted([
        d for d in data.get("daily", {})
        if d.startswith(snap_month) and d < snap_date
    ])
    monthly_snap = data["daily"].get(prev_month_dates[-1], {}) if prev_month_dates else {}

    all_reviews = []

    for b in BRANCHES:
        bid = str(b["id"])
        if bid not in results:
            continue
        r = results[bid]

        prev_total = baseline_snap.get(bid, {}).get("total_snap",
                     data.get("branches", {}).get(bid, {}).get("overall", 0))
        raw_delta = r["total"] - prev_total

        prev_monthly = monthly_snap.get(bid, {}).get("monthly", 0)
        monthly = prev_monthly + max(raw_delta, 0)

        data["daily"][snap_date][bid] = {
            "total_snap":   r["total"],
            "daily_count":  max(raw_delta, 0),
            "raw_delta":    raw_delta,
            "has_deletion": raw_delta < 0,
            "monthly":      monthly,
            "star_rating":  r["stars"],
            "yesterday_reviews": len(r["reviews"]),
        }
        data["branches"][bid] = {
            "id":          b["id"],
            "name":        b["name"],
            "agm":         b["agm"],
            "overall":     r["total"],
            "star_rating": r["stars"],
            "monthly":     monthly,
        }

        for rev in r["reviews"]:
            all_reviews.append({
                **rev,
                "branch_id":   b["id"],
                "branch_name": b["name"],
                "agm":         b["agm"],
            })

    # Save yesterday's review details
    detail_dir = DATA_FILE.parent / "reviews_detail"
    detail_dir.mkdir(parents=True, exist_ok=True)
    detail_path = detail_dir / f"{yesterday}.json"

    # Merge with existing if file already exists (re-run safety)
    existing = []
    if detail_path.exists():
        try:
            with open(detail_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass
    existing_ids = {r["review_id"] for r in existing}
    merged = existing + [r for r in all_reviews if r["review_id"] not in existing_ids]

    with open(detail_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print(f"  Saved {len(merged)} reviews to {detail_path}")

    # Log entry
    data.setdefault("logs", []).insert(0, {
        "ran_at":        run_time,
        "snap_date":     snap_date,
        "yesterday":     yesterday,
        "baseline_date": baseline_date,
        "success":       success,
        "failed":        len(failed),
        "failed_names":  failed,
        "total_yesterday_reviews": len(merged),
    })
    data["logs"] = data["logs"][:50]
    data["last_updated"] = run_time

    save_data(data)
    print(f"  Saved reviews.json — {success}/36 branches")


# ── Main ─────────────────────────────────────────────────────────────────────

async def main():
    now_ist = ist_now()
    # Lock snap_date ONCE — never re-derive inside engine functions
    snap_date = now_ist.date().strftime("%Y-%m-%d")
    yesterday = (now_ist - timedelta(days=1)).date().strftime("%Y-%m-%d")
    run_time  = datetime.now(timezone.utc).isoformat()

    print(f"=== Google Reviews Scraper ===")
    print(f"  Run time : {now_ist.strftime('%Y-%m-%d %H:%M IST')}")
    print(f"  Snap date: {snap_date}")
    print(f"  Scanning : {yesterday} (yesterday IST)")
    print()

    results, success, failed = await run_all(snap_date, yesterday)

    print(f"\n=== Results: {success}/36 branches ===")
    if failed:
        print(f"  Failed: {', '.join(failed)}")

    if success == 0:
        print("FATAL: 0 branches succeeded. reviews.json NOT updated.")
        sys.exit(1)

    save_results(results, success, failed, snap_date, yesterday, run_time)
    print("=== Done ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"FATAL: {e}")
        traceback.print_exc()
        sys.exit(1)
