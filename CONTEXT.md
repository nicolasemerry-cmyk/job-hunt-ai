# Job Hunt — Claude Code Context

## What this folder is
A job scanner that scrapes 15 creative job boards for relevant video/film production roles and generates an HTML report. Run it twice a week.

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

## The sites being scanned
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

## Known issues
Most sites block simple scrapers or require JavaScript to render. Currently only a handful return results (If You Could Jobs and Tomorrow Worldwide confirmed working). If Nicolas wants better coverage, the fix is to upgrade the failing sites to use Playwright (headless browser). He can ask for that as a separate task.

## Keywords being matched
**Include:** video editor, video producer, videographer, content producer, film editor, post-production, motion graphics, filmmaker, camera operator, colour grading, digital content, content creator, DaVinci Resolve colourist

**Exclude:** casting, audition, actor, model, theatre, accountant, software engineer, data analyst, legal, senior, head of, lead, principal, director of, chief, executive producer, creative director

## Who Nicolas is (for context)
Video producer, director, and editor. Currently employed at Doctor Mix (820K+ subscriber YouTube channel). Based in London. Age 23, about to turn 24. Key skills: Premiere Pro, DaVinci Resolve, After Effects, Sony mirrorless cameras, colour grading, motion graphics, live streaming, multicam editing, studio lighting, on-set audio.

## Role selection criteria — IMPORTANT
When recommending or selecting roles to apply for, apply these filters:

**Level:** Junior or mid-level only. Exclude anything with "Senior", "Head of", "Lead", "Principal", "Director of", "Executive Producer", or "Creative Director" in the title. Nicolas has ~4 years freelance + less than 1 year full-time studio experience — he is not a senior hire.

**Good fit signals:** roles that mention video production, editing, post-production, content creation, camera operation, or similar. Bonus if they mention Premiere Pro, DaVinci Resolve, After Effects, YouTube, or social video.

**Poor fit signals:** roles that are primarily marketing, copywriting, graphic design (no video), photography only, or require 5+ years experience. Flag these as low-fit rather than recommending them.

**When summarising results**, group into: Strong fit / Possible fit / Probably not — so Nicolas can quickly decide what to pursue.
