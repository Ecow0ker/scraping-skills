# Advanced Scrapling

Read this only when the basic scripts are not enough.

## Installation

For a full project environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install "scrapling[all]"
scrapling install --force
```

Use `scrapling[all]` by default for research data projects because sources often need JavaScript rendering, browser sessions, or batch crawling.

Read `engine-selection.md` before replacing Scrapling with direct Playwright or Codex Browser/Chrome.

## Fetch Mode Mapping

- Use `Fetcher` for static pages and API-like responses.
- Use `DynamicFetcher` or `DynamicSession` when JavaScript rendering is required.
- Use `StealthyFetcher` or `AsyncStealthySession` only when the user has permission and ordinary browser fetching fails on protected public pages.
- Use `Spider` when the task needs many pages, retries, allowed domains, download delays, robots.txt, checkpointing, or streaming. Default repeated page requests to a 10-second delay.

## Boundary With Playwright And Codex Browser

- Keep Scrapling as the default production fetch/archive layer for public and reproducible datasets.
- Use direct Playwright when the task needs complex clicks, infinite scroll, file downloads after interaction, or a reproducible authorized browser session.
- Use Codex Chrome/local Chrome by default to inspect interactive pages, discover network endpoints, debug selectors, or support a user's manual login/verification/confirmation. Use Codex Browser only as a fallback for simple public visual debugging. Do not make Chrome or Codex Browser the final repeatable data pipeline.
- If the Codex Chrome Extension is missing or disabled, use the official Chrome setup-assist flow and wait for the user to install/enable it. Do not run native-host installer scripts or copy browser secrets.
- After Playwright, Chrome, or Codex Browser reveals a JSON/API endpoint, convert the collection back into Python HTTP/Scrapling whenever practical.

## Useful Scrapling Features

- `robots_txt_obey = True` for polite crawls.
- `download_delay=10` and `concurrent_requests_per_domain=1` for default rate control.
- `crawldir` for pause and resume.
- `development_mode = True` only while developing selectors.
- `capture_xhr` when data are loaded through background API calls.
- `adaptive=True` only after a selector has been saved and the site structure changed.

## Keep Hidden From Users

Do not explain Fetcher classes, Playwright parameters, TLS fingerprints, proxies, CDP, or browser internals unless the user explicitly asks. Translate these choices into research workflow language.
