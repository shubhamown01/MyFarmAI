# Browser Automation Agent Skill

## Purpose
Navigate and interact with web pages using the user's real Chromium browser profile via Browser Control. Preserves authenticated sessions, cookies, and extensions.

## When to Use
- Opening websites and navigating pages
- Clicking elements, filling forms, typing text
- Taking screenshots of web pages
- Extracting data from web pages
- Managing browser tabs
- Tasks requiring authenticated sessions (logged-in sites)

## Tools Available
- `@browser` — Main skill command for browser automation workflows
- `browser-control` MCP tools (execute, session_new, session_adopt, snapshot, screenshot, recording)
- Playwright MCP (fallback for headless operations)

## Workflow
1. **Inspect**: `@browser Check setup and show extension status` → `@browser Navigate to <URL> and snapshot page`
2. **Act**: `@browser Click element <ref>`, `@browser Type "<text>" into <ref>`, `@browser Scroll <direction>`
3. **Verify**: `@browser Screenshot and confirm result`, `@browser Extract <data> from page`

## Key Principles
- Use semantic element refs (e1, e2...) from ARIA snapshots, not coordinates
- Preserve user's browser session — never close tabs the user didn't create
- One action per snapshot cycle; verify before proceeding
- Pause for human on CAPTCHA, MFA, passkey, or sensitive forms
- Never submit payments, delete data, or change account settings without explicit approval

## Integration
- Invoked via `@browser` skill in OpenCode
- Browser Control relay runs on `127.0.0.1:19989`
- Extension directory: `/home/mrknight/.cache/opencode/npm/@opencode-ai/browser-control@latest/.../extension/dist`
- Requires Chrome/Chromium with Browser Control extension loaded (manual install)

## Example Usage
```
@browser Open https://example.com and return the page title
@browser Search for "MyFarmAI" on GitHub and click the first result
@browser Fill login form at https://app.example.com with credentials from secure store
```