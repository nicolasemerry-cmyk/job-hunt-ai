#!/usr/bin/env python3
"""
Job Scanner - Nicolas Merry
Scans creative job boards for relevant video/film production roles.
Run with: python job_scanner.py
Results saved to: job_report.html
"""

import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import Stealth
import json
import os
import re
from datetime import datetime
from urllib.parse import urljoin

# --- CONFIGURATION -----------------------------------------------------------

# -- Relevance model -----------------------------------------------------------
# Matching is done with WORD BOUNDARIES (see _has / is_relevant), so "editor"
# no longer matches "editorial", etc.
#
# Scope (confirmed by Nicolas): video editing/post, videography/camera, and
# video & content producing. NOT motion graphics/animation. Plain "Producer"/
# "Editor" only count when there's a video/film/content signal (or the source
# board is film/video-only).

# Strong keywords - relevant on their own.
STRONG_KEYWORDS = [
    "video editor", "video producer", "video producer and editor", "videographer",
    "video content", "video editing", "content producer", "content creator",
    "film editor", "filmmaker", "film maker", "post-production", "post production",
    "post producer", "camera operator", "social media video", "music video",
    "colour grading", "color grading", "director of photography",
    "videographer and editor", "video editor and motion",
]

# Generic role words - only count WITH a video/film/content context word, OR when
# the source board is video/film-only (VIDEO_SITES).
GENERIC_ROLES = ["editor", "producer", "edit assistant", "assistant editor"]

CONTEXT = [
    "video", "film", "footage", "content", "social", "youtube", "broadcast",
    "commercial", "advert", "documentary", "post-production", "post production",
    "reels", "cinema", "vfx", "motion", "videograph", "camera", "grading", "edit suite",
]

EXCLUDE_TERMS = [
    # Irrelevant industries
    "casting", "audition", "actor", "actress", "model", "voiceover", "voice over",
    "theatre", "theater", "dancer", "musician", "accountant", "finance",
    "developer", "software engineer", "data analyst", "solicitor", "legal",
    # Audio/sound - wrong discipline
    "dubbing", "sound editor", "audio editor", "audio producer", "audio engineer",
    "sound designer", "sound mixer", "re-recording", "dialogue editor", "foley",
    "podcast", "radio", "audio post", "music producer",
    # Print / words / static-design noise
    "editorial", "copywriter", "copy editor", "photo editor", "picture editor",
    "sub-editor", "subeditor", "animator", "animation", "illustrator", "illustration",
    "graphic designer",
    # Management / ops noise
    "studio manager", "account manager", "project manager", "office manager",
    "studio coordinator", "production manager", "production coordinator",
    # Wrong-discipline producers
    "event producer", "experiential", "activation", "welfare", "engagement producer",
    "concert", "course", "gallery producer", "studio producer", "live ob",
    "challenge producer", "task producer", "script editor", "script supervisor",
    "culinary", "food producer", "cooking", "brand experience",
    # Too senior / management
    "senior", "head of", "lead", "principal", "director of", "chief", "vp",
    "vice president", "executive producer", "creative director", "associate director",
    "series producer", "series director", "supervising producer", "line producer",
    "executive director",
    # Wrong sector
    "social media manager", "marketing manager", "brand manager",
    "performance marketing", "growth marketing",
]

# "director of photography" contains "director of" (an exclude) but IS wanted.
ALLOW_OVERRIDE = ["director of photography"]

# Boards that are exclusively film/TV/video - on these, a bare "Producer"/"Editor"
# is treated as in-scope without needing an extra context word.
VIDEO_SITES = {
    "FilmIndustryJobs", "ProductionBase", "Mandy (Crew Jobs UK)", "ScreenSkills",
    "GrapevineJobs", "ShowbizJobs (UK)", "The Talent Manager", "APA Jobs",
    "Tomorrow Worldwide",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
}

STATE_FILE = "last_seen.json"

# --- SITES CONFIG -------------------------------------------------------------

SITES = [
    {
        "name": "Creative Lives in Progress",
        "url": "https://creativelivesinprogress.com/opportunities",
        "job_selector": "a",
        "title_attr": "text",
        "link_attr": "href",
        "link_filter": "/opportunities/",
    },
    {
        "name": "UAL Creative Opportunities",
        "url": "https://creativeopportunities.arts.ac.uk/vacancies/",
        "job_selector": "a.vacancy-title, h2 a, h3 a, .job-title a",
        "title_attr": "text",
        "link_attr": "href",
        "link_filter": "/vacancies/",
    },
    {
        "name": "If You Could Jobs",
        "url": "https://www.ifyoucouldjobs.com/jobs",
        "job_selector": "a",
        "title_attr": "text",
        "link_attr": "href",
        "link_filter": "/jobs/",
    },
    {
        "name": "Run The Check",
        "url": "https://www.runthecheck.com/",
        "job_selector": "a",
        "title_attr": "text",
        "link_attr": "href",
        "link_filter": None,
    },
    {
        "name": "Workculture",
        "url": "https://workculture.uk/jobs/",
        "job_selector": "h2 a, h3 a, .job-title a, article a",
        "title_attr": "text",
        "link_attr": "href",
        "link_filter": "/jobs/",
    },
    {
        "name": "Doors Open",
        "url": "https://www.doorsopen.co/jobs",
        "job_selector": "a",
        "title_attr": "text",
        "link_attr": "href",
        "link_filter": "/jobs/",
    },
    {
        "name": "Create Jobs Community",
        "url": "https://community.createjobslondon.org/opportunities",
        "job_selector": "a",
        "title_attr": "text",
        "link_attr": "href",
        "link_filter": None,
    },
    {
        "name": "Creative Access (Junior, London)",
        "url": "http://opportunities.creativeaccess.org.uk/jobs/junior?geo_location=London%2C+UK&lon=-0.1275862&lat=51.5072178&radius=80&locationType=locality&location=London&country=United+Kingdom&administrative_area_level_1=England&field_job_experience=1410",
        "job_selector": "a",
        "title_attr": "text",
        "link_attr": "href",
        "link_filter": "/jobs/",
    },
    {
        "name": "Major Players",
        "url": "https://www.majorplayers.co/en/jobs",
        "job_selector": "a",
        "title_attr": "text",
        "link_attr": "href",
        "link_filter": "/jobs/",
    },
    {
        "name": "Tomorrow Worldwide",
        "url": "https://tomorrow-worldwide.com/job-listings/",
        "job_selector": "a",
        "title_attr": "text",
        "link_attr": "href",
        "link_filter": None,
    },
    {
        "name": "Mandy (Crew Jobs UK)",
        "url": "https://www.mandy.com/uk/jobs/crew/",
        "job_selector": "a",
        "title_attr": "text",
        "link_attr": "href",
        "link_filter": "/job/",
    },
    {
        "name": "ProductionBase",
        "url": "https://www.productionbase.co.uk/film-tv-jobs",
        "job_selector": "a",
        "title_attr": "text",
        "link_attr": "href",
        "link_filter": "/job",
    },
    {
        "name": "The Talent Manager",
        "url": "https://www.thetalentmanager.com/jobs",
        "job_selector": "a",
        "title_attr": "text",
        "link_attr": "href",
        "link_filter": "/job",
    },
    {
        "name": "ScreenSkills",
        "url": "https://www.screenskills.com/jobs/",
        "job_selector": "a",
        "title_attr": "text",
        "link_attr": "href",
        "link_filter": "/jobs/",
    },
    {
        "name": "Burberry Careers",
        "url": "https://burberrycareers.com/go/Search-and-Apply/",
        "job_selector": "a",
        "title_attr": "text",
        "link_attr": "href",
        "link_filter": None,
    },
    {
        "name": "GrapevineJobs",
        "url": "https://www.grapevinejobs.co.uk/jobs-in-media-broadcast-tv-video-post-production",
        "job_selector": "a.color-button-1",
        "title_attr": "text",
        "link_attr": "href",
        "link_filter": "/mediajobs/",
        "title_selector": "h3.job-title",
        "dedup_by": "url",
    },
    {
        "name": "FilmIndustryJobs",
        "url": "https://www.filmindustryjobs.co.uk/jobs",
        "job_selector": "a.fij-job-card-link",
        "title_attr": "text",
        "link_attr": "href",
        "link_filter": "/jobs/",
        "title_selector": "h3",
        "dedup_by": "url",
    },
    {
        "name": "ShowbizJobs (UK)",
        "url": "https://www.showbizjobs.com/jobs/location/country/gb",
        "job_selector": "a",
        "title_attr": "text",
        "link_attr": "href",
        "link_filter": "/jid-",
        "dedup_by": "url",
    },
]

# --- RSS FEEDS CONFIG ---------------------------------------------------------

RSS_FEEDS = [
    {
        "name": "APA Jobs",
        "url": "https://www.a-p-a.net/jobs/feed/",
    },
    {
        "name": "music-jobs.com UK",
        "url": "https://www.music-jobs.com/uk/rss/rss_jobs-44.xml",
    },
]

# --- HELPERS ------------------------------------------------------------------

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def _has(term, text):
    """Word-boundary match (tolerates a trailing plural 's').
    Prevents 'editor' from matching 'editorial' and 'event' from missing
    'events'. `text` should be pre-padded with spaces."""
    return re.search(r"(?<![a-z])" + re.escape(term) + r"s?(?![a-z])", text) is not None

def is_relevant(title, source=""):
    t = " " + title.lower().strip() + " "
    if len(title.strip()) < 5:
        return False
    # Excludes win, unless the title is explicitly allow-listed.
    if not any(a in t for a in ALLOW_OVERRIDE):
        for ex in EXCLUDE_TERMS:
            if _has(ex, t):
                return False
    # Strong keywords are relevant on their own.
    if any(_has(kw, t) for kw in STRONG_KEYWORDS):
        return True
    # Generic role words need a video/film/content signal, or a video-only board.
    if any(_has(g, t) for g in GENERIC_ROLES):
        if source in VIDEO_SITES or any(_has(c, t) for c in CONTEXT):
            return True
    return False

def fetch_jobs(page, site):
    """Fetch job listings from a site using a Playwright browser page."""
    results = []
    try:
        try:
            page.goto(site["url"], wait_until="networkidle", timeout=30000)
        except PlaywrightTimeoutError:
            # Page took too long to go fully idle - use whatever loaded
            pass

        content = page.content()
        soup = BeautifulSoup(content, "lxml")

        seen = set()
        seen_urls = set()
        dedup_by = site.get("dedup_by", "title")
        title_sel = site.get("title_selector")
        links = soup.select(site["job_selector"])

        for tag in links:
            href = tag.get("href", "")

            if not href:
                continue

            # Filter by link pattern if specified
            if site["link_filter"] and site["link_filter"] not in href:
                continue

            # Make absolute URL
            if href.startswith("http"):
                full_url = href
            else:
                full_url = urljoin(site["url"], href)

            # Extract title - from a child/parent element if title_selector is set
            if title_sel:
                title_el = tag.select_one(title_sel)
                if not title_el:
                    container = tag.find_parent("tr") or tag.find_parent("article") or tag.find_parent("li")
                    title_el = container.select_one(title_sel) if container else None
                title = title_el.get_text(strip=True) if title_el else ""
            else:
                title = tag.get_text(separator=" ", strip=True)

            if not title:
                continue

            # Deduplicate by URL (for sites where each job URL appears multiple times)
            # or by title (default)
            key = full_url if dedup_by == "url" else title
            if key in seen:
                continue
            seen.add(key)

            # Collapse the same job appearing under two anchor texts (same URL).
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            if is_relevant(title, site["name"]):
                results.append({"title": title, "url": full_url})

    except Exception as e:
        results.append({"title": f"! Error fetching site: {e}", "url": site["url"], "error": True})

    return results


def fetch_rss_jobs(feed):
    """Fetch job listings from an RSS feed using requests + ElementTree."""
    results = []
    try:
        resp = requests.get(feed["url"], headers=HEADERS, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")
        for item in items:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            if title and link and is_relevant(title, feed["name"]):
                results.append({"title": title, "url": link})
    except Exception as e:
        results.append({"title": f"! Error fetching RSS: {e}", "url": feed["url"], "error": True})
    return results

# --- HTML REPORT --------------------------------------------------------------

def generate_report(all_results, new_counts, date_str):
    total_new = sum(new_counts.values())
    total_found = sum(len(v["jobs"]) for v in all_results.values())

    site_rows = ""
    for site_name, data in all_results.items():
        jobs = data["jobs"]
        new = new_counts.get(site_name, 0)
        status = f'<span class="badge new">{new} new</span>' if new else '<span class="badge seen">no new</span>'
        error = any(j.get("error") for j in jobs)

        if error:
            status = '<span class="badge error">error</span>'

        job_items = ""
        for j in jobs:
            is_new = j.get("is_new", False)
            new_tag = ' <span class="new-tag">NEW</span>' if is_new else ""
            if j.get("error"):
                job_items += f'<li class="error-item">! {j["title"]}</li>'
            else:
                li_class = ' class="new-item"' if is_new else ""
                job_items += f'<li{li_class}><a href="{j["url"]}" target="_blank">{j["title"]}</a>{new_tag}</li>'

        if not jobs:
            job_items = "<li class='none'>No matching jobs found</li>"

        site_rows += f"""
        <div class="site-block{'  error-block' if error else ''}">
            <div class="site-header">
                <h2>{site_name}</h2>
                <div class="site-meta">{status} &nbsp;-&nbsp; <a href="{data['url']}" target="_blank">open site </a></div>
            </div>
            <ul>{job_items}</ul>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Job Scan - {date_str}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f0f0f; color: #e0e0e0; padding: 32px 24px; }}
  .header {{ max-width: 860px; margin: 0 auto 36px; border-bottom: 1px solid #2a2a2a; padding-bottom: 20px; }}
  .header h1 {{ font-size: 22px; font-weight: 600; color: #86E0A8; letter-spacing: -0.3px; }}
  .header p {{ font-size: 13px; color: #777; margin-top: 6px; }}
  .summary {{ display: flex; gap: 20px; margin-top: 14px; }}
  .stat {{ background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 12px 18px; }}
  .stat .num {{ font-size: 26px; font-weight: 700; color: #86E0A8; }}
  .stat .label {{ font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }}
  .sites {{ max-width: 860px; margin: 0 auto; display: grid; gap: 16px; }}
  .site-block {{ background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 10px; padding: 20px 24px; }}
  .site-block.error-block {{ border-color: #3a2020; }}
  .site-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }}
  .site-header h2 {{ font-size: 15px; font-weight: 600; color: #ccc; }}
  .site-meta {{ font-size: 12px; color: #555; }}
  .site-meta a {{ color: #555; text-decoration: none; }}
  .site-meta a:hover {{ color: #86E0A8; }}
  .badge {{ font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: 4px; }}
  .badge.new {{ background: #1a3a26; color: #86E0A8; }}
  .badge.seen {{ background: #1e1e1e; color: #444; }}
  .badge.error {{ background: #3a1a1a; color: #e08686; }}
  ul {{ list-style: none; display: flex; flex-direction: column; gap: 8px; }}
  li a {{ font-size: 14px; color: #aaa; text-decoration: none; line-height: 1.4; }}
  li a:hover {{ color: #86E0A8; }}
  li.new-item a {{ color: #e0e0e0; font-weight: 500; }}
  .new-tag {{ font-size: 10px; font-weight: 700; background: #1a3a26; color: #86E0A8; padding: 2px 6px; border-radius: 3px; margin-left: 6px; vertical-align: middle; }}
  li.none {{ font-size: 13px; color: #444; font-style: italic; }}
  li.error-item {{ font-size: 13px; color: #e08686; }}
  .footer {{ max-width: 860px; margin: 32px auto 0; font-size: 12px; color: #444; text-align: center; }}
</style>
</head>
<body>
<div class="header">
  <h1>Job Scan Report</h1>
  <p>Run on {date_str}</p>
  <div class="summary">
    <div class="stat"><div class="num">{total_new}</div><div class="label">New since last run</div></div>
    <div class="stat"><div class="num">{total_found}</div><div class="label">Total matching jobs</div></div>
    <div class="stat"><div class="num">{len(all_results)}</div><div class="label">Sites scanned</div></div>
  </div>
</div>
<div class="sites">
{site_rows}
</div>
<div class="footer">Generated by job_scanner.py - Keywords: video editor, video producer, videographer, content producer, filmmaker, motion graphics, post-production</div>
</body>
</html>"""
    return html

# --- MAIN ---------------------------------------------------------------------

def main():
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    print(f"\n  Job Scanner -- {date_str}")
    print("-" * 50)

    state = load_state()
    all_results = {}
    new_counts = {}

    # -- RSS feeds (no Playwright needed) --------------------------------------
    for feed in RSS_FEEDS:
        print(f"  Scanning: {feed['name']}...", end=" ", flush=True)
        jobs = fetch_rss_jobs(feed)
        site_key = feed["name"]
        prev_urls = set(state.get(site_key, []))
        new_count = sum(1 for j in jobs if not j.get("error") and j["url"] not in prev_urls)
        for job in jobs:
            if not job.get("error"):
                job["is_new"] = job["url"] not in prev_urls
        new_counts[site_key] = new_count
        all_results[site_key] = {"jobs": jobs, "url": feed["url"]}
        state[site_key] = [j["url"] for j in jobs if not j.get("error")]
        status = f"OK  {len(jobs)} found ({new_count} new)" if jobs and not any(j.get("error") for j in jobs) else "!!  error or no results"
        print(status)

    stealth = Stealth()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for site in SITES:
            print(f"  Scanning: {site['name']}...", end=" ", flush=True)

            page = browser.new_page()
            page.set_extra_http_headers(HEADERS)
            stealth.apply_stealth_sync(page)

            jobs = fetch_jobs(page, site)
            page.close()

            site_key = site["name"]
            prev_urls = set(state.get(site_key, []))
            new_count = 0

            for job in jobs:
                if not job.get("error"):
                    job["is_new"] = job["url"] not in prev_urls
                    if job["is_new"]:
                        new_count += 1

            new_counts[site_key] = new_count
            all_results[site_key] = {"jobs": jobs, "url": site["url"]}

            state[site_key] = [j["url"] for j in jobs if not j.get("error")]

            status = f"OK  {len(jobs)} found ({new_count} new)" if jobs and not any(j.get("error") for j in jobs) else "!!  error or no results"
            print(status)

        browser.close()

    save_state(state)

    # Collect new jobs as flat list for email/JSON output
    new_jobs_list = []
    for site_name, data in all_results.items():
        for job in data["jobs"]:
            if job.get("is_new") and not job.get("error"):
                new_jobs_list.append({
                    "title": job["title"],
                    "url": job["url"],
                    "source": site_name,
                })

    with open("new_jobs.json", "w", encoding="utf-8") as f:
        json.dump({"date": date_str, "new_count": len(new_jobs_list), "jobs": new_jobs_list}, f, indent=2)

    report_html = generate_report(all_results, new_counts, date_str)
    report_file = "job_report.html"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_html)

    total_new = sum(new_counts.values())
    total_found = sum(len(v["jobs"]) for v in all_results.values())

    print("-" * 50)
    print(f"  Done. {total_found} matching jobs found, {total_new} new since last run.")
    print(f"  Report saved: {report_file}\n")

if __name__ == "__main__":
    main()
