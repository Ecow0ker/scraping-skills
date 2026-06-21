# Login and Human Interaction

Use this reference for sites that require login, captcha, QR scan, anti-bot confirmation, or manual confirmation.

Also read `engine-selection.md` before choosing local Chrome/Codex Chrome, Playwright, the in-app Browser fallback, or a manual-download workflow.

## Rules

- Confirm the user has legitimate access before continuing.
- Do not ask for passwords in chat.
- Do not store credentials, cookies, or tokens in logs or output data.
- Do not try to bypass captchas or access controls.
- Prefer official API/export or manual download when available.
- Prefer the user's local Chrome for any browser-based login, captcha, anti-bot confirmation, QR scan, MFA, or manual download.
- If the Codex Chrome Extension is missing or disabled, automatically start the official setup-assist flow: run readiness checks, open the official install/enable page when appropriate, wait for the user to complete Chrome's confirmation, and retry the Chrome connection.
- Use the in-app Browser only when Chrome is unavailable, the user explicitly asks for it, or the task is simple public visual debugging without account state.
- Do not stop at the first login/captcha/confirmation page. Open local Chrome, remind the user what to complete, require explicit completion confirmation, then resume collection. Use built-in Codex confirmation/user-input UI only when the current mode/runtime exposes it.

## Scenario Routing

- **Official API/export after login**: Open local Chrome for the user to log in and use the official export/API path. Wait for the downloaded file path or authorized API response, then continue from that source dataset.
- **Manual file download is enough**: Guide the user to download the file and provide the local file path; continue from the file rather than automating the private website.
- **One-time authorized extraction**: Use local Chrome and keep the extraction narrow. Wait for the user to complete login/verification/confirmation and explicitly confirm completion, then continue.
- **Repeated authorized panel collection**: Prefer official API/export. If unavailable and permitted, use Playwright with a local session state file stored outside final data folders.
- **Existing signed-in Chrome session is required**: Use Codex Chrome for exploration or one-time extraction. Wait for the user to confirm the session is ready. Do not copy cookies/tokens into project outputs.
- **Public page has JavaScript but no login**: Use Scrapling `DynamicFetcher` first; use Playwright only when complex interaction is required.
- **Captcha, MFA, QR scan, anti-bot confirmation, or identity check appears**: Open local Chrome and pause for the user to complete it. Ask for an explicit "verification completed, continue" confirmation before re-checking the page. Do not solve, bypass, or outsource verification.
- **Paywall, account limit, or unclear rights**: Stop and ask for permission, a licensed export, or another source.

## Workflow

1. Explain why human interaction is needed.
2. Confirm which scenario above applies.
3. Preserve the current task state: URL, requested columns, page range, time range, output folder, and evidence already saved.
4. Start or instruct a local Chrome session only if API/export/manual file is not enough; if the Codex Chrome Extension is missing or disabled, complete the setup-assist flow first; use another visible browser only as a documented fallback.
5. Tell the user exactly what to complete on the opened Chrome page.
6. Ask the user whether verification/login/confirmation is complete. If the current Codex mode/runtime exposes a built-in user-input or confirmation control, use it with a required choice labeled like `我已完成验证，继续抓取` / `I completed verification, continue`; otherwise ask for an explicit text reply such as `已完成验证`.
7. Wait. Do not continue by guessing, bypassing, reading hidden credentials, or relying only on a timeout/page change.
8. After the user explicitly confirms completion, refresh/re-check the page or endpoint.
9. Continue only within the authorized session and requested scope.
10. Save raw data and metadata, but redact session secrets.

## User Confirmation Prompt

After opening Chrome for verification, use a short prompt that names the site and exact task:

```text
我已经在本机 Chrome 打开需要验证的页面。请在 Chrome 中完成登录/验证码/确认访问。完成后，如果当前 Codex 界面出现确认选项，请选择“我已完成验证，继续抓取”；如果没有确认选项，请回复“已完成验证”。
```

Do not continue until that explicit confirmation is received.

## Stop Conditions

Stop and ask the user when:

- the user cannot complete login/verification/confirmation or declines to continue
- the site blocks access after login/verification/confirmation
- the Codex Chrome Extension or native host remains unavailable after the official setup-assist flow
- the page asks for additional identity verification
- the content appears paywalled or outside the user's permission
- personal sensitive data are visible and not necessary for the research task
