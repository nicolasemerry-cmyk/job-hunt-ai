# Job Hunt — Claude Code Context

## What this folder is
A job scanner that scrapes 20 creative job boards/feeds for relevant video/film production roles and generates an HTML report. Runs automatically twice a week via GitHub Actions (Mon + Thu 8am UTC) and emails the results; can also be run manually.

## YOUR INSTRUCTIONS — DO THIS NOW
You are reading this as the start of a new session. Do the following immediately, without waiting for further input:
1. Run `job_scanner.py`
2. Open the generated `job_report_YYYY-MM-DD.html` in the browser
3. Report back how many new jobs were found and on which sites
4. Then wait for Nicolas to ask anything further

## How to run it
```
python job_scanner.py
```
(Dependencies are already installed: `requests`, `beautifulsoup4`, `lxml`)

---

## STEP 2 — Generating Applications (only when Nicolas asks)

After the scan, Nicolas will review the report and tell you which jobs he wants to apply for.
When he says something like "generate applications for jobs 2 and 5" or "apply for the ProductionBase one":

1. Read `cv.html` and `cover_letter_template.html` from this folder
2. Fetch the job listing URL from the report to understand the role requirements
3. For each role, produce two files:
   - `cv_[company-name].html` — the CV with the Professional Profile lightly tailored to the role
   - `cover_letter_[company-name].html` — the cover letter with all {{PLACEHOLDERS}} filled in with real, specific content
4. Open each file in the browser so Nicolas can review

### CV tailoring rules
- Adjust the Professional Profile to reflect the specific role type (lean into music video experience for music roles, broadcast for TV roles, etc.)
- Reorder skills columns if needed so most relevant appears first
- Do not add experience that isn't in the base cv.html
- Keep it to one page — do not change the visual design

### Cover letter rules
- Replace all {{PLACEHOLDERS}} with real content
- Para 2: reference 2–3 specific concrete experiences from the CV matching the job — name tools, outputs, scale
- Para 3: show genuine research into the company — reference a specific project, client, or approach
- Tone: confident, direct. No clichés. No "I am passionate about". One page maximum.
- If no hiring manager name available, use "Hiring Team"

## Files in this folder
- `job_scanner.py` — the main scanner script
- `CONTEXT.md` — this file
- `last_seen.json` — auto-generated, tracks which jobs have been seen before (do not delete)
- `job_report_YYYY-MM-DD.html` — output reports, one per run

## How "new" detection works
After each run, `last_seen.json` is updated with all job URLs found. On the next run, anything not in that file is marked NEW in the report. Never delete `last_seen.json` or the new-detection resets.

## The sites being scanned (20 sources: 18 scraped + 2 RSS)
Scraped with Playwright (headless Chromium):
1. Creative Lives in Progress — https://creativelivesinprogress.com/opportunities
2. UAL Creative Opportunities — https://creativeopportunities.arts.ac.uk/vacancies/
3. If You Could Jobs — https://www.ifyoucouldjobs.com/jobs
4. Run The Check — https://www.runthecheck.com/
5. Workculture — https://workculture.uk/jobs/
6. Doors Open — https://www.doorsopen.co/jobs
7. Create Jobs Community — https://community.createjobslondon.org/opportunities
8. Creative Access (Junior, London) — http://opportunities.creativeaccess.org.uk/jobs/junior?geo_location=London...
9. Major Players — https://www.majorplayers.co/en/jobs
10. Tomorrow Worldwide — https://tomorrow-worldwide.com/job-listings/
11. Mandy (Crew Jobs UK) — https://www.mandy.com/uk/jobs/crew/
12. ProductionBase — https://www.productionbase.co.uk/film-tv-jobs
13. The Talent Manager — https://www.thetalentmanager.com/jobs
14. ScreenSkills — https://www.screenskills.com/jobs/
15. Burberry Careers — https://burberrycareers.com/go/Search-and-Apply/
16. GrapevineJobs — https://www.grapevinejobs.co.uk/jobs-in-media-broadcast-tv-video-post-production
17. FilmIndustryJobs — https://www.filmindustryjobs.co.uk/jobs
18. ShowbizJobs (UK) — https://www.showbizjobs.com/jobs/location/country/gb

RSS feeds (requests + ElementTree, no Playwright):
19. APA Jobs — https://www.a-p-a.net/jobs/feed/
20. music-jobs.com UK — https://www.music-jobs.com/uk/rss/rss_jobs-44.xml

## Known issues
Many sites block simple scrapers or require JavaScript, so coverage varies run to run.
As of the 2026-06-24 GitHub run, results came back from: APA Jobs, music-jobs.com UK,
If You Could Jobs, Tomorrow Worldwide, The Talent Manager, GrapevineJobs, and
FilmIndustryJobs. The others returned nothing that run (blocked, empty, or selector
drift). If Nicolas wants better coverage, individual site selectors/handling can be
upgraded as a separate task.

## How relevance matching works (updated 2026-06-24, scanner commit `319f523`)
Matching uses **word boundaries** (`_has()` in `job_scanner.py`), not naive substring
search — so "editor" no longer matches "editorial", etc. Confirmed scope with Nicolas:
**keep** video editing/post, videography/camera, and video & content producing;
**drop** motion graphics/animation and standalone non-video producer roles.

Three layers in `is_relevant(title, source)`:
1. **STRONG_KEYWORDS** — relevant on their own: video editor, video producer,
   videographer, video content, content producer, content creator, film editor,
   filmmaker, post-production, post producer, camera operator, social media video,
   music video, colour/color grading, director of photography.
2. **GENERIC_ROLES** (editor, producer, assistant editor) — only count when the title
   also has a **CONTEXT** word (video, film, content, social, footage, broadcast,
   documentary, motion, camera, grading…) OR the board is a **VIDEO_SITES** one
   (FilmIndustryJobs, Prod