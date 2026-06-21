# Ethics and Compliance

Use this skill only for data the user is authorized to access.

## Defaults

- Prefer official APIs, public downloads, datasets, and sitemaps before scraping pages.
- Respect robots.txt and website terms.
- Use a default 10-second delay between repeated page requests and conservative concurrency.
- Do not scrape personal sensitive data unless the user has a lawful basis and a clear minimization plan.
- Do not bypass paywalls, authentication, captchas, or access controls.
- Keep source URLs, timestamps, and raw evidence for auditability.

## Protected or Login Content

If content requires login, captcha, anti-bot confirmation, or manual confirmation, ask the user to confirm that they have permission. Open local Chrome for human-assisted completion by default, wait for the user to reply that it is done, and never store passwords, tokens, or cookies in logs or final datasets. If the Codex Chrome Extension is missing or disabled, use only the official setup-assist flow and leave Chrome's extension install/enable confirmation to the user.

## Publication

Before data are shared or published, remove credentials, cookies, raw personal data, and any fields outside the research purpose.
