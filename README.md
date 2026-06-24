# Job Scanner — Nicolas Merry

Scans 15 creative job boards for video/film production roles and generates an HTML report highlighting anything new since your last run.

## Setup (one time only)

1. Make sure you have Python 3 installed (you almost certainly do on Mac)
2. Install dependencies:
   ```
   pip3 install requests beautifulsoup4 lxml
   ```

## Running the scanner

```
python3 job_scanner.py
```

That's it. It will:
- Scan all 15 sites
- Filter for relevant roles (video editor, producer, videographer, etc.)
- Flag anything new since your last run
- Save a report as `job_report_YYYY-MM-DD.html`

Open the HTML file in any browser to review results.

## How "new" works

The script saves a `last_seen.json` file after each run containing all the job URLs it found. Next time you run it, anything not in that file is marked **NEW** in the report. So run it twice a week and you'll only see what's changed.

## Customising keywords

Open `job_scanner.py` and edit the lists near the top:

- `KEYWORDS_TITLE` — job title keywords to match (e.g. add `"documentary"`)
- `EXCLUDE_TERMS` — terms that filter jobs OUT (e.g. add `"senior"` if you want to exclude senior roles)

## Sites scanned

1. Creative Lives in Progress
2. UAL Creative Opportunities
3. If You Could Jobs
4. Run The Check
5. Workculture
6. Doors Open
7. Create Jobs Community
8. Creative Access (Junior, London)
9. Major Players
10. Tomorrow Worldwide
11. Mandy (Crew Jobs UK)
12. ProductionBase
13. The Talent Manager
14. ScreenSkills
15. Burberry Careers
