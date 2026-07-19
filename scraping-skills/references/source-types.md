# Source Types

Use this reference to classify a website before choosing a script.

Read `engine-selection.md` when the source is dynamic, interactive, authenticated, blocked, or requires a browser decision.

## Decision Rules

- **Single page**: One URL contains the needed content. Use `single_page_extract.py`.
- **Known air-quality history source**: For aqistudy city air-quality history, use `aqistudy_extract.py` so the CSV contains city-date observations instead of page text. Pass `--language zh` for Chinese user requests and `--language en` for English user requests. Prefer `--output-parent .` from the workspace root and let the script auto-version sibling crawl/final-data folders there.
- **Batch URLs**: The user already has a CSV of URLs. Use `batch_url_extract.py`.
- **Downloaded file or local table**: If the user already has CSV, Excel, JSONL, DTA, or another structured file, treat that file as a data source. Clean, reshape, audit, and export the dataset instead of scraping the website again.
- **Listing plus detail pages**: A listing page links to many detail pages, such as jobs, housing, products, procurement notices, or announcements. Use `listing_detail_spider.py`.
- **Search result pages**: Treat as listing pages. Record the query, filters, page number, and observed time as metadata.
- **Dynamic page**: Important content appears only after JavaScript runs. Start with ordinary fetching; if data are empty or incomplete, look for the page's data endpoint before upgrading to browser fetching.
- **API response**: If network inspection or page source reveals JSON endpoints, prefer collecting the JSON endpoint with raw response metadata and observation-level rows.
- **Login, verification, or confirmation page**: Read `login-and-human-interaction.md` and `engine-selection.md`. Open local Chrome by default, enter waiting-for-user state, remind the user what to complete, require explicit "verification completed, continue" confirmation, then continue within the authorized scope. Use built-in Codex confirmation controls only when available; otherwise require a text reply.
- **Existing signed-in Chrome state**: Use Codex Chrome only for exploration or user-assisted one-time access; if the Codex Chrome Extension is missing or disabled, start the official setup-assist flow first. Build a reproducible pipeline with official export/API or Playwright session state if repeated collection is required.
- **Captcha, MFA, QR scan, anti-bot confirmation, or identity check**: Open local Chrome by default, pause for user completion, and resume only after the user explicitly confirms completion through an available Codex confirmation control or replies that verification is complete. Do not automate around verification.

## Escalation

Escalate only as needed:

1. static HTTP request
2. Scrapling dynamic browser fetch
3. Playwright for complex interaction or reproducible authorized sessions
4. local Chrome/Codex Chrome for user-assisted login, verification, confirmation, or manual downloads
5. custom spider with checkpointing

Keep the final user explanation in research terms, not scraper internals.

## Output Parent

Default to the current workspace/project root as the output parent. Put the crawl/evidence folder and final-data folder directly under that root. Do not add a `test-runs/` or task-named wrapper folder unless the user explicitly requests an isolated test workspace.

For generic sources, derive folder names from the research object, not the engine. Use sibling folders such as `招聘数据抓取/` plus `招聘最终数据/`, or `job-postings-data/` plus `job-postings-final-data/`. First runs have no suffix; repeated runs add `V2`, `V3` or `-v2`, `-v3`.
