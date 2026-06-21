# Engine Selection

Use the lightest tool that can produce a reproducible research dataset. Do not expose engine names to low-technical users unless they ask.

## Decision Table

| Scenario | Use | Why | Guardrail |
|---|---|---|---|
| Public API, CSV, JSON, or download link is available | Python HTTP plus `save_raw_response.py`; Scrapling `Fetcher` is acceptable for archiving | Most reproducible and easiest to audit | Prefer the data endpoint over rendered HTML |
| Public static HTML page | Scrapling `Fetcher` | Fast, simple, preserves raw evidence | Fall back to `urllib` only if Scrapling is unavailable |
| Public listing plus detail pages | `listing_detail_spider.py`; Scrapling fetchers | Handles repeated pages, provenance, and row-level outputs | Default to 10 seconds between page requests and conservative concurrency |
| JavaScript-rendered public page | First inspect for background API; if none, Scrapling `DynamicFetcher` | Keeps the skill in one Python stack | Use browser fetching only after static/API attempts fail |
| Complex page interaction, scrolling, clicking filters, or XHR discovery | Playwright during development; optionally convert discovered API calls back to Python/Scrapling | Best for exploring and capturing network behavior | Do not leave a fragile click script if an API endpoint is found |
| One-time visual inspection or selector debugging | Codex in-app browser / Browser plugin | Good shared view for debugging public pages | Do not use it as the final data pipeline |
| Site needs interaction, login, captcha, QR scan, MFA, anti-bot confirmation, manual download, or the user's signed-in session | Codex Chrome extension / local Chrome by default; if the Codex Chrome Extension is missing or disabled, start the official setup-assist flow | Uses the user's browser state without asking for passwords | Do not export cookies/tokens into project outputs |
| Reproducible authorized collection behind login | Playwright with a user-created local session state, or an official authenticated API/export | More stable than manual browser clicking | Store session state outside final data; never commit secrets |
| Login, QR scan, MFA, captcha, anti-bot confirmation, or identity check | Enter waiting-for-user state in local Chrome, then resume after the user confirms completion | User must complete authorization or confirmation | Never bypass verification or ask for passwords in chat |
| Paywalled, blocked, or unclear authorization | Stop and ask the user for permission/source alternative | Avoids unauthorized collection | Prefer official API, data export, or licensed download |
| Anti-bot friction on public pages | Scrapling stealth only with explicit legitimate permission | May help with browser fingerprint mismatches | Do not bypass captchas, paywalls, or access controls |

## Recommended Order

1. Look for official download, API, or data endpoint.
2. Try static Scrapling fetching and archive raw evidence.
3. Use dynamic Scrapling fetching only when JavaScript is necessary.
4. Use Playwright to discover interactions or authenticated workflows.
5. Use local Chrome/Codex Chrome by default for user-assisted login/verification/confirmation or manual downloads. If the Codex Chrome Extension is missing or disabled, follow Chrome Extension Readiness below before falling back. Use Codex in-app Browser only for simple public visual debugging or when Chrome is unavailable.
6. After opening Chrome, remind the user what to complete and require explicit "verification completed, continue" confirmation. Use a built-in user-input/confirmation control only when the current Codex mode/runtime exposes one; otherwise require a text reply.
7. After the user completes login/verification and explicitly confirms it, re-check the page/API and continue extraction within the authorized scope.
8. Stop only when authorization is unclear, the user cannot complete verification, the user declines, secrets would need to be copied, or the site remains blocked after user action.

## Login Choice

- If login is only needed to download a file manually, open local Chrome, guide the user to log in/download, and ask for the downloaded file path; then continue from that local file.
- If login is needed for a one-time authorized extraction, open local Chrome, wait for the user to finish and explicitly confirm completion, then extract only the requested fields.
- If login is needed for repeated panel collection, ask for an official API/export first. If none exists, build a Playwright workflow with a local session file outside the dataset folders.
- If the site shows captcha/MFA/QR verification or an anti-bot confirmation page, open local Chrome, pause, and let the user complete it, then resume from the verified page only after explicit completion confirmation. Do not automate around it.

## Waiting-For-User State

When verification, login, or a site confirmation page blocks collection:

1. Preserve the target URL, requested fields, output folder, and current evidence.
2. Open local Chrome/Codex Chrome by default. Use the in-app Browser only if Chrome is unavailable, the user explicitly requests it, or no account/session is involved and the task is simple visual debugging.
3. Tell the user exactly what to complete on the opened Chrome page.
4. Ask the user whether it is complete. If the current Codex mode/runtime exposes built-in confirmation controls, require a choice labeled like `我已完成验证，继续抓取`; otherwise require an explicit text reply such as `已完成验证`.
5. After explicit confirmation, refresh/re-check the page or endpoint.
6. Continue extraction if data are accessible; otherwise record the remaining blocker in the review report.

## Chrome Extension Readiness

For any interactive scenario, try local Chrome first.

1. Attempt a lightweight Codex Chrome connection check.
2. If it fails, wait 2 seconds and retry once.
3. If Chrome is not running, ask to launch Chrome and wait for the user's response.
4. If the Codex Chrome Extension is missing, open the official Codex Chrome Extension page only through the official Chrome setup-assist path, then wait for the user to install it in Chrome.
5. If the extension is installed but disabled, open the Chrome extension manager only through the official setup-assist path, then wait for the user to enable it.
6. Retry the Chrome connection after the user confirms installation/enabling.
7. Do not run native-host installer scripts or copy cookies/tokens. If the native host or extension-backed install path is broken, tell the user to reinstall the Chrome plugin from the Codex plugin UI.

## Crawl Pacing

- Default multi-page crawls to one page every 10 seconds.
- Keep concurrency at 1 unless the source explicitly permits faster collection.
- If the user requests a faster crawl, explain the risk and keep the safer delay unless the source is an official API/download designed for bulk access.

## Output Rule

Engine choice must not change the research contract. Final outputs still need observation-level CSV/JSONL/DTA where appropriate, raw evidence, metadata, and a review report.
