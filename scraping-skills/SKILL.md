---
name: scraping-skills
description: Build reproducible public web datasets for research data collection and organization using Python and Scrapling. Use when collecting or structuring web data for research, including prices, jobs, housing, procurement, announcements, air quality, organization pages, news indexes, panels, batch URL extraction, raw evidence archiving, quality checks, or human-assisted Chrome login/verification workflows.
---

# Scraping Skills

## Purpose

Use this skill to turn public web pages into reproducible research datasets. The CSV is the analysis dataset, not a page dump: rows should be meaningful observations such as city-day air-quality records, job postings, prices, organizations, announcements, or housing listings. Keep the user-facing workflow simple: ask about the research question, source URLs, desired fields, collection frequency, and output format; hide Scrapling and browser details unless the task requires them.

Python is the implementation language. Keep Scrapling as the default fetch/archive engine, installed with `pip install "scrapling[all]"` when a project needs a full environment. Scrapling does not define the final dataset: use it to fetch pages, discover links, handle dynamic pages, and preserve evidence; use source-specific extractors or APIs to create observation-level CSV files.

## Workflow

1. Clarify only the missing research details:
   - research object or hypothesis
   - source URL or URL list
   - required fields
   - one-time collection or repeated panel tracking
   - output format: CSV, JSONL, Excel, dta, Parquet, or DuckDB
2. Classify the source. Read `references/source-types.md` if the source shape is unclear.
3. Choose the lightest collection engine. Read `references/engine-selection.md` when the page is dynamic, interactive, authenticated, blocked, or unclear.
4. Choose the simplest script:
   - `scripts/aqistudy_extract.py` for China city-day air-quality history from aqistudy
   - `scripts/single_page_extract.py` for one page
   - `scripts/batch_url_extract.py` for a CSV of URLs
   - `scripts/listing_detail_spider.py` for listing pages with detail links
   - `scripts/quality_report.py` after data is collected
5. Save raw evidence and structured data separately. Every record must keep source URL, final URL, fetch time, status code, content hash, and raw file path.
6. Generate a review report before presenting results. Chinese requests use `审查报告.md` with Chinese body text; English requests use `quality_report.md`.
7. If a page requires login, captcha, anti-bot confirmation, or any human confirmation, read `references/login-and-human-interaction.md`, open the user's local Chrome by default, preserve task state, remind the user what to verify, and require explicit "verification completed, continue" confirmation before resuming. Use a built-in confirmation/user-input control only when the current Codex runtime exposes one; otherwise use an explicit text reply. If the Codex Chrome Extension is missing or disabled, start the official Chrome extension setup-assist flow and retry after the user installs/enables it.
8. Write ordinary skill outputs directly under the current workspace/project root. Do not create an extra wrapper such as `test-runs/<scenario-name>/` unless the user explicitly asks for an isolated test run.

## Resource Routing

- Read `references/aqistudy-air-quality.md` when collecting aqistudy air-quality history or when users mention city air quality/AQI examples.
- Read `references/aqistudy-rules-fragment.md` when users mention aqistudy, hot cities, current-month AQI, or the URL `https://www.aqistudy.cn/historydata/index.php`.
- Read `references/engine-selection.md` before choosing Scrapling, Playwright, Codex Browser, Codex Chrome, or a human-assisted flow.
- Read `references/research-schemas.md` when fields, panel keys, Chinese field names, or dta output need design.
- Read `references/quality-checks.md` before writing or interpreting a review/quality report.
- Read `references/ethics-and-compliance.md` before large crawls, login workflows, protected pages, or sensitive data collection.
- Read `references/advanced-scrapling.md` only when ordinary HTTP fetching fails, JavaScript rendering is needed, the crawl is multi-page, or the site changes structure.

## Defaults

- Prefer public downloads and APIs before scraping rendered pages.
- Start with ordinary HTTP fetching, then upgrade to browser fetching only when needed.
- Use Scrapling as the default reproducible Python fetch/archive engine. Use Playwright for complex interactions or reproducible authorized sessions. Use local Chrome/Codex Chrome by default for any user-assisted login, captcha, anti-bot confirmation, QR scan, MFA, or manual download. If the Codex Chrome Extension is not installed or not enabled, automatically run the Chrome readiness checks, open the official Codex Chrome Extension install/enable path when allowed, wait for the user to complete Chrome's confirmation, then retry. Use Codex in-app Browser only when Chrome is unavailable, the user explicitly asks for it, or the task is simple public visual debugging. After the user completes login/verification/confirmation and explicitly confirms completion, continue with Python/API/Scrapling or Playwright as appropriate; do not use Chrome or the in-app Browser as the final repeatable dataset pipeline.
- When the user does not specify fields, infer research-useful columns from the source. For air quality, default to city, month, date, AQI, quality level, PM2.5, PM10, SO2, NO2, CO, and O3.
- When the user specifies fields or columns, collect those fields and keep required provenance columns after them.
- Match output language to the user's language. Chinese requests should use Chinese folder names and Chinese column names; English requests should use English folder names and English column names.
- By default, use the current workspace/project root as the output parent. Create the crawl/evidence folder and final-data folder as direct children of that root, not inside `test-runs/` or a task-named wrapper folder. Use a different parent only when the user specifies one.
- For aqistudy outputs, create two sibling directories under the output parent: a crawl/evidence folder and a final-data folder. Chinese names are `aqistudy数据抓取` and `aqistudy最终数据`; English names are `aqistudy-data` and `aqistudy-final-data`. The first run has no version suffix; the second run uses `V2` or `-v2`, then `V3` or `-v3`.
- For aqistudy, default final formats are CSV, JSONL, and Stata DTA. Keep `_dta_labels.json` beside DTA files when Stata-safe variable names replace Chinese column names.
- For aqistudy Chinese crawl folders, include `代码文件/运行方式.md` and `代码文件/一键运行.py`. The visible rerun command should have no parameters: `python 代码文件/一键运行.py`.
- Do not treat page title, raw body text, or HTML as the final CSV unless the research object is the page itself.
- Use polite settings by default: robots.txt where applicable, 10 seconds between repeated page requests, and conservative concurrency.
- Preserve original page evidence even when also creating cleaned text for analysis.
- Use Chinese field names for Chinese sources when the user wants researcher-friendly output; use English field names for English sources or code-facing metadata.
- Do not automatically bypass login, paywalls, captchas, anti-bot checks, or authorization boundaries. Open the user's local Chrome, wait for the user to complete legitimate verification/login/confirmation, and require explicit completion confirmation before continuing. Use built-in Codex user-input/confirmation controls only when available in the current mode/runtime; do not claim a modal, popup, checkbox, or button exists if it is not available. Otherwise ask for an explicit text reply. Continue only within the authorized scope. For a missing Codex Chrome Extension, use only the official install/enable flow and leave Chrome's final extension installation confirmation to the user. If Chrome is unavailable, record that fallback and use another visible browser only with the user's awareness.

## Output Layout

Create project outputs in this shape directly under the current workspace/project root unless the user asks otherwise. For Chinese users, localize folder names while keeping the same roles. Avoid task wrapper folders such as `test-runs/<scenario>/` during normal skill use.

```text
aqistudy-data/
├── config/
├── data/
│   ├── raw/
│   ├── processed/
│   └── metadata/
├── reports/
├── logs/
└── code/
aqistudy-final-data/
└── final CSV/JSONL/DTA
```

For recurring collections, include stable `entity_id`, `observed_at`, `region`, and `category` fields when available.
