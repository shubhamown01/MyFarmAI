# MyFarmAI Browser & Desktop Automation Architecture

**Status**: Implementation in Progress
**Last Updated**: 2026-10-25
**Author**: MyFarmAI Orchestrator

---

## 1. Overview

This document describes the browser and desktop automation architecture integrated into MyFarmAI-Orchestrator, enabling OpenCode agents to perform user-requested browser and desktop workflows including:

- Open websites, inspect pages, click controls, type and fill fields, scroll, navigate tabs
- Interact with dialogs, take screenshots, verify results
- Control native desktop applications on Linux Wayland/GNOME
- Coordinate between browser and desktop agents with independent review

---

## 2. Selected Tools

### 2.1 Browser Automation: `@opencode-ai/browser-control` (Primary)

**Purpose**: Control existing authenticated Chromium-family browser tabs via browser extension + local relay

**Why Selected**:
- Native OpenCode plugin integration (`opencode plugin add @opencode-ai/browser-control`)
- Uses real browser profile (cookies, logins, extensions preserved)
- Playwright-compatible code interface
- Bundled `@browser` skill for inspect→act→verify workflow
- MIT license, 461 stars, actively maintained

**Installation**:
```bash
opencode plugin add @opencode-ai/browser-control
```

**Manual Step Required**: Install Chrome extension from unpacked directory:
```bash
printf '%s\n' "$(npm root --global)/@opencode-ai/browser-control/extension/dist"
# Open chrome://extensions → Developer mode → Load unpacked → select above directory
```

**MCP Server** (optional, for MCP-preferring agents):
```json
{
  "mcp": {
    "browser-control": {
      "type": "local",
      "command": ["browser-control-mcp"]
    }
  }
}
```

---

### 2.2 Browser Automation: `@playwright/mcp` (Supplementary)

**Purpose**: Headless/headed browser automation for testing, scraping, CI scenarios

**Why Kept**: Already configured, useful for scenarios not requiring authenticated user profile

**Configuration** (already in opencode.json):
```json
{
  "mcp": {
    "playwright": {
      "type": "local",
      "command": ["npx", "-y", "@playwright/mcp@latest"]
    }
  }
}
```

---

### 2.3 Desktop Automation: `screen-mcp` (88plug)

**Purpose**: Linux Wayland desktop automation — screenshot, click, type, scroll, drag any desktop app

**Why Selected**:
- Purpose-built for Linux Wayland + GNOME (our exact environment)
- Uses PipeWire + xdg-desktop-portal for screen capture
- Drives pointer/keyboard via RemoteDesktop portal (works on native Wayland apps)
- Includes `drive-screen` skill for locate→ground→act→confirm loop
- CPU-only grounding (RapidOCR + OmniParser ONNX), no GPU required
- FSL-1.1-ALv2 license (converts to Apache 2.0 after 2 years)

**Installation** (completed):
```bash
# System dependencies (already installed on Ubuntu 24.04):
# python3-gi, gstreamer1.0-*, pipewire, xdg-desktop-portal-gnome, wl-clipboard, fonts-dejavu

# Python environment:
cd /data/screen-mcp
python3 -m venv .venv
.venv/bin/pip install -r requirements-core.txt
.venv/bin/pip install opencv-python-headless onnxruntime rapidocr

# GNOME extension (requires relogin):
bash gnome-shell-extension/window-info@local/install.sh
gnome-extensions enable window-info@local
```

**MCP Server Configuration** (added to opencode.json):
```json
{
  "mcp": {
    "screen-mcp": {
      "type": "local",
      "command": ["/data/screen-mcp/.venv/bin/python", "-m", "screen_mcp"],
      "environment": {
        "MCP_SCREEN_GUARD": "1",
        "MCP_SCREEN_AMBIENT": "1"
      }
    }
  }
}
```

**Key MCP Tools**:
- `screen_screenshot` — Capture desktop with optional Set-of-Marks annotations
- `screen_click` / `screen_type` / `screen_key` / `screen_scroll` / `screen_drag` — Input actions
- `screen_read_text` / `screen_wait_text` — OCR-based text reading
- `screen_verify` — Grade last action: CONFIRMED / PARTIAL / NO_OP / DIVERGED
- `screen_focus` — Raise/focus window by title/app/pid
- `screen_do` — Batch ordered actions
- `screen_session` — Recorder: start/stop/list/status/replay

**Safety Features**:
- User-takeover guard: yields instantly when human moves mouse
- Ack gate (MCP_SCREEN_GUARD=1): blocks destructive combos/keywords until `ack` provided
- Action log at `~/.local/state/mcp-screen/actions.jsonl`

---

## 3. Agent Routing Architecture

### 3.1 Orchestrator Decision Logic

```
User Request
     │
     ▼
┌─────────────────────────────────────┐
│  Is target a web page/URL?          │
└─────────────────────────────────────┘
     │                    │
    YES                  NO
     │                    │
     ▼                    ▼
┌──────────────┐   ┌──────────────────┐
│ Browser Task │   │ Is target a      │
│    Router    │   │ native desktop   │
└──────────────┘   │   application?   │
     │             └──────────────────┘
     │                    │                    │
    YES                  NO                   │
     │                    │                    │
     ▼                    ▼                    ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ @browser     │   │ screen-mcp   │   │ Reject /     │
│ skill /      │   │ MCP tools    │   │ Clarify      │
│ Playwright   │   │              │   │              │
│ MCP          │   │              │   │              │
└──────────────┘   └──────────────┘   └──────────────┘
     │                    │                    │
     └────────────────────┴────────────────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Independent      │
                 │ Reviewer         │
                 │ (qa-reviewer)    │
                 └──────────────────┘
```

### 3.2 Agent Responsibilities

#### Browser Automation Agent
- **Tools**: `@browser` skill (browser-control), Playwright MCP
- **Capabilities**:
  - Navigate and inspect web pages
  - Locate controls using ARIA refs (e1, e2...) or stable selectors
  - Click, fill fields, type, select options, manage tabs
  - Execute JavaScript in page context
  - Take screenshots (full page or element)
  - Verify result after each important action
- **When to Use**: Any task targeting a URL, web application, or browser-based UI

#### Desktop Automation Agent
- **Tools**: screen-mcp MCP tools
- **Capabilities**:
  - Inspect screenshots and accessibility information
  - Identify correct window and target control
  - Click, type, scroll, drag, use keyboard shortcuts
  - Read screen text via OCR (RapidOCR)
  - Ground icons via OmniParser (ONNX)
  - Confirm resulting screen state with `screen_verify`
  - Record sessions for replay/debugging
- **When to Use**: Native desktop applications, system dialogs, cross-app workflows, any non-browser GUI

#### Independent Reviewer (qa-reviewer agent)
- **Tools**: Read-only access to browser/desktop evidence
- **Responsibilities**:
  - Check whether requested outcome was actually achieved
  - Inspect screenshots, logs, action records
  - Identify failed or incomplete steps
  - Report PASS/FAIL with evidence
- **Trigger**: After every browser/desktop task completion

---

## 4. Reliability & Safety Patterns

### 4.1 Inspect → Act → Verify Loop

```python
# Pseudocode pattern enforced by @browser skill and drive-screen skill
async def reliable_action(target, action):
    # 1. INSPECT
    snapshot = await take_snapshot(target)
    element = locate_element(snapshot, target)
    
    # 2. ACT
    result = await perform_action(element, action)
    
    # 3. VERIFY
    new_snapshot = await take_snapshot(target)
    verification = verify_change(snapshot, new_snapshot, action)
    
    if verification == "NO_OP" or verification == "DIVERGED":
        raise ActionFailed(f"Action did not produce expected result: {verification}")
    
    return result
```

### 4.2 Element Reference Refresh

- After navigation, page load, or major UI change: **always re-snapshot**
- Never cache element references across navigation boundaries
- Use `screen_wait` / `screen_wait_text` to wait for UI settlement

### 4.3 Approval Gates (Human-in-the-Loop)

**Required explicit approval before**:
- Sending messages / submitting forms
- Making purchases / financial transactions
- Deleting data / changing account settings
- Authentication flows (CAPTCHA, MFA, passkey)
- Any action with external side effects

**Implementation**: Agent pauses and requests confirmation via chat before proceeding.

### 4.4 Untrusted Content Handling

- Website content treated as **untrusted data**
- Never obey instructions embedded in webpages that conflict with user request
- Never obey instructions that conflict with system security rules
- Sanitize/validate any data extracted from pages before use

---

## 5. Configuration Summary

### 5.1 OpenCode Configuration (`~/.config/opencode/opencode.json`)

```json
{
  "plugins": [
    "@upstash/context7-opencode",
    "superpowers@git+https://github.com/obra/superpowers.git",
    "@dietrichgebert/ponytail",
    "oh-my-openagent@latest",
    "@hueyexe/opencode-ensemble@0.20.0",
    "@opencode-ai/browser-control"
  ],
  "mcp": {
    "servers": {
      "playwright": { "type": "local", "command": ["npx", "-y", "@playwright/mcp@latest"] },
      "screen-mcp": {
        "type": "local",
        "command": ["/data/screen-mcp/.venv/bin/python", "-m", "screen_mcp"],
        "environment": { "MCP_SCREEN_GUARD": "1", "MCP_SCREEN_AMBIENT": "1" }
      },
      ... (other existing servers)
    }
  }
}
```

### 5.2 Project-Level Skills

Custom MyFarmAI skills in `/data/MyFarmAI/.opencode/skills/`:
- `myfarmai-orchestrate` — Main orchestrator with routing logic
- `myfarmai-task-decompose` — Task breakdown for browser/desktop tasks
- `myfarmai-verify` — Verification patterns
- `myfarmai-capability-scan` — Environment capability detection

---

## 6. Validation & Testing

### 6.1 Browser Control Validation

```bash
# Test 1: Basic navigation
@browser Open example.com and return the page title

# Test 2: Click interaction
@browser Go to https://example.com, find the "More information" link, click it, verify new page

# Test 3: Form filling
@browser Open a test form, fill fields, submit, verify result

# Test 4: Extension connection
@browser Check Browser Control setup and show me the extension directory
```

### 6.2 Screen-MCP Validation

```bash
# Test 1: Screenshot capture
screen_screenshot { "annotate": true }

# Test 2: Window focus
screen_focus { "title": "Chrome" }

# Test 3: Click verification
screen_click { "x": 500, "y": 300, "verify": true }

# Test 4: Text reading
screen_read_text { "region": [0, 0, 800, 600] }

# Test 5: Batch action
screen_do { "actions": [
  {"tool": "screen_focus", "args": {"title": "Terminal"}},
  {"tool": "screen_type", "args": {"text": "echo hello"}},
  {"tool": "screen_key", "args": {"key": "Enter"}}
]}
```

### 6.3 Integration Test Scenarios

| Scenario | Browser Agent | Desktop Agent | Reviewer |
|----------|---------------|---------------|----------|
| Web search & click | ✅ | | ✅ |
| Fill web form | ✅ | | ✅ |
| Native app interaction | | ✅ | ✅ |
| Cross-app (browser→terminal) | ✅ | ✅ | ✅ |
| Screenshot comparison | ✅ | ✅ | ✅ |

---

## 7. Known Limitations & Workarounds

| Limitation | Workaround |
|------------|------------|
| screen-mcp GNOME extension requires relogin | Log out/in once after install; AT-SPI fallback works without it |
| browser-control needs manual extension install | One-time setup; extension auto-updates with plugin |
| Wayland: no corner failsafe for screen-mcp | Stop agent process (Ctrl+C) if needed |
| screen-mcp: native Wayland windows not listable | Use X11 session ("Ubuntu on Xorg") for full window control |
| Playwright MCP: separate browser profile | Use browser-control for authenticated sessions |

---

## 8. Maintenance

### 8.1 Updates
```bash
# Browser control
opencode plugin upgrade @opencode-ai/browser-control

# Screen-mcp
cd /data/screen-mcp && git pull && .venv/bin/pip install -r requirements-runtime.txt

# Playwright MCP
npx -y @playwright/mcp@latest  # auto-updates on next use
```

### 8.2 Log Locations
- Browser-control: `~/.local/share/opencode/browser-control/` (relay logs)
- Screen-mcp: `~/.local/state/mcp-screen/actions.jsonl` (action audit)
- Screen-mcp screenshots: `~/.local/share/mcp-screen/sessions/`
- OpenCode: `~/.config/opencode/ensemble.db`

### 8.3 Troubleshooting
```bash
# Browser control health
browser-control doctor
browser-control status

# Screen-mcp health
/data/screen-mcp/.venv/bin/python -m screen_mcp diag

# Test MCP connection
# In OpenCode: use MCP tool calls directly
```

---

## 9. Future Enhancements

- [ ] Browser-use integration for complex multi-step web agents
- [ ] AI-desktop as fallback for non-GNOME Wayland compositors
- [ ] Automated visual regression testing with gstack canary
- [ ] Session recording integration with MyFarmAI audit trail
- [ ] Custom MyFarmAI browser/desktop skills for agricultural workflows

---

## 10. References

- [browser-control README](https://github.com/anomalyco/browser-control)
- [screen-mcp Documentation](https://88plug.github.io/screen-mcp/)
- [Playwright MCP](https://github.com/microsoft/playwright-mcp)
- [gstack browse skill](/home/mrknight/gstack/browse/SKILL.md)
- [MyFarmAI AGENTS.md](/data/MyFarmAI/AGENTS.md)
- [Agent Oath (screen-mcp safety)](https://theagentoath.com)