# MyFarmAI Browser & Desktop Automation Architecture

## Overview
This document describes the browser and desktop automation integration for MyFarmAI, enabling the orchestrator and agents to perform user-requested web and native desktop workflows.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MyFarmAI Orchestrator                           │
│  (Task decomposition, routing, approval gates, verification)        │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Browser Agent    │ │ Desktop Agent    │ │ Independent      │
│ (@browser)       │ │ (screen-mcp)     │ │ Reviewer         │
│                  │ │                  │ │ (qa-reviewer)    │
│ • Navigate web   │ │ • Native apps    │ │ • Verify outcome │
│ • Click, type    │ │ • System UI      │ │ • Check evidence │
│ • Screenshots    │ │ • OCR reading    │ │ • Certify done   │
│ • ARIA refs      │ │ • Keyboard/mouse │ │ • Read-only      │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Browser Control  │ │ screen-mcp MCP   │ │ Evidence         │
│ (MV3 extension + │ │ (PipeWire +      │ │ (Screenshots,    │
│  local relay)    │ │  xdg-desktop-    │ │  logs, extracted │
│                  │ │  portal +        │ │  data)           │
│ • Real Chrome    │ │  GNOME Shell)    │ │                  │
│ • Auth sessions  │ │                  │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

## Component Details

### 1. Browser Automation Agent
- **Skill**: `browser-automation-agent` (invoked via `@browser`)
- **Backend**: Browser Control (@opencode-ai/browser-control)
- **Transport**: Local Node relay (127.0.0.1:19989) ↔ MV3 Chrome extension
- **Browser**: User's real Chrome/Chromium profile (preserves auth, cookies, extensions)
- **Capabilities**:
  - Navigate, click, type, scroll, tabs
  - ARIA snapshot element refs (e1, e2...)
  - Screenshots with labeled elements
  - Session management (adopt user tabs, never close user tabs)
  - CDP guardrails (read-only mode, block destructive commands)

### 2. Desktop Automation Agent
- **Skill**: `desktop-automation-agent` (via screen-mcp MCP tools)
- **Backend**: screen-mcp (88plug)
- **Transport**: MCP stdio → Python server → PipeWire/xdg-desktop-portal
- **Platform**: Linux Wayland + GNOME (only)
- **Capabilities**:
  - Screen capture (monitors/regions) with numbered marks
  - Click, type, scroll, drag, hotkeys
  - OCR text extraction (RapidOCR)
  - Icon grounding (OmniParser ONNX)
  - Window focus/management
  - Frame diff change detection
  - Session recording/replay

### 3. Independent Reviewer
- **Agent**: `automation-reviewer` / `qa-reviewer`
- **Mode**: Read-only verification
- **Inputs**: Screenshots, logs, extracted data, network traces
- **Outputs**: PASS/FAIL/PARTIAL with evidence

## Routing Rules

| Task Type | Agent | Backend |
|-----------|-------|---------|
| Web page (HTTP/HTTPS) | Browser Agent | Browser Control |
| Authenticated web app | Browser Agent | Browser Control |
| Native Linux app (GTK/Qt) | Desktop Agent | screen-mcp |
| System UI (file dialog, settings) | Desktop Agent | screen-mcp |
| Cross-app workflow | Desktop Agent | screen-mcp |
| OCR from any window | Desktop Agent | screen-mcp |
| Headless CI testing | (existing) | Playwright MCP |

## Reliability Patterns

### Inspect → Act → Verify Loop
```
1. Inspect: screenshot / ARIA snapshot / OCR
2. Act: ONE atomic action (click, type, hotkey)
3. Verify: screenshot + screen_verify / data check
4. Repeat until done
```

### Safety Guards
- **User-takeover**: screen-mcp stops on mouse movement
- **Ack guard**: Blocks destructive combos (Alt+F4, Ctrl+W) until confirmed
- **CDP guardrails**: Browser Control blocks destructive commands in read-only mode
- **Approval gates**: Human confirmation required for submissions, deletions, payments
- **Human-only challenges**: Pause for CAPTCHA, MFA, passkey

### Session Management
- Browser Control: 15-min idle cleanup, user tabs never closed
- screen-mcp: Portal token cached at `~/.config/mcp-screen`
- Both: Isolated per-task sessions

## Installation & Configuration

### Browser Control
```bash
# Added as OpenCode plugin
opencode plugin add @opencode-ai/browser-control

# Manual: Install Chrome extension
# chrome://extensions → Developer mode → Load unpacked
# Extension dir: ~/.cache/opencode/npm/@opencode-ai/browser-control@latest/.../extension/dist
```

### screen-mcp
```bash
# System deps (Ubuntu)
sudo apt install python3-gi python3-gi-cairo gir1.2-gstreamer-1.0 \
  gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
  gstreamer1.0-libav pipewire pipewire-pulse xdg-desktop-portal-gnome \
  wl-clipboard fonts-dejavu

# Python venv
cd /data/screen-mcp
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# GNOME Shell extension (requires Wayland re-login)
gnome-shell-extension/window-info@local/install.sh
gnome-extensions enable window-info@local
```

### OpenCode Config (opencode.json)
```json
{
  "plugin": ["@opencode-ai/browser-control", ...],
  "mcp": {
    "servers": {
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
}
```

## Skills Created

| Skill | Path | Purpose |
|-------|------|---------|
| browser-automation-agent | `.opencode/skills/browser-automation-agent/` | Web automation workflow |
| desktop-automation-agent | `.opencode/skills/desktop-automation-agent/` | Desktop automation workflow |
| automation-reviewer | `.opencode/skills/automation-reviewer/` | Independent verification |

## Orchestrator Integration

Updated `.opencode/agents/myfarmai-orchestrator.md` with:
- Agent permissions for automation agents
- Routing rules (web → browser, native → desktop)
- Reliability patterns (inspect→act→verify)
- Approval gates and security boundaries
- Session boundary definitions

## Validation

Run validation script:
```bash
/data/MyFarmAI/scripts/validate-automation.sh
```

Functional tests:
```bash
# Browser test
@browser Open https://example.com and return the page title

# Desktop test (after Wayland re-login)
screen_screenshot --annotate=true
screen_verify
```

## Manual Setup Required

1. **Chrome Extension**: Load unpacked extension in Chrome (one-time)
2. **python3-gi-cairo**: `sudo apt install python3-gi-cairo`
3. **Wayland Re-login**: Log out/in to activate GNOME Shell extension
4. **Verify**: Run validation script after re-login

## Security Considerations

- Browser Control uses existing Chrome profile — no new credentials stored
- screen-mcp runs with user permissions, no elevated privileges
- User-takeover guard prevents runaway automation
- Ack guard prevents accidental destructive actions
- No secrets or credentials in automation code
- All evidence stored locally (`~/.config/mcp-screen/`, browser profile)

## Maintenance

- Browser Control: Update via `opencode plugin add @opencode-ai/browser-control`
- screen-mcp: `cd /data/screen-mcp && git pull && .venv/bin/pip install -r requirements.txt`
- GNOME Extension: Re-run install.sh after GNOME upgrades
- Validation: Run script after any system/browser updates

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| Browser Control not connecting | Check extension loaded, relay port 19989 free |
| screen-mcp "portal not available" | Re-login Wayland, check xdg-desktop-portal-gnome running |
| OCR not working | Install rapidocr: `.venv/bin/pip install rapidocr-onnxruntime` |
| GNOME extension not loading | Re-login required; check `gnome-extensions list --enabled` |
| MCP server not starting | Check venv path, python version (3.10+), deps installed |

## References

- Browser Control: https://github.com/anomalyco/browser-control
- screen-mcp: https://github.com/88plug/screen-mcp
- The Agent Oath: https://theagentoath.com
- OpenCode Plugin API: https://opencode.ai/docs/plugins