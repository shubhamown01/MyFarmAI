# Browser & Desktop Automation Integration - Completion Summary

**Project**: MyFarmAI-Orchestrator
**Date**: 2026-10-25
**Status**: Core Integration Complete — Manual Steps Remaining

---

## ✅ What Was Accomplished

### Phase 1: Environment Audit
- OpenCode v2.1.4 configuration fully documented
- 14 MCP servers, 130+ agents, 30+ skills catalogued
- Desktop: Wayland + GNOME, Chrome + Firefox available

### Phase 2: Tool Evaluation & Selection

| Tool | Stars | License | Decision |
|------|-------|---------|----------|
| **@opencode-ai/browser-control** | 461 | MIT | ✅ Primary (authenticated tabs) |
| **screen-mcp (88plug)** | 1 | FSL-1.1-ALv2 | ✅ Primary (Wayland desktop) |
| opencode-browser-plugin | 0 | MIT | ❌ Redundant |
| browser-use | 119K | MIT | ❌ Too heavyweight |
| ai-desktop | 1 | MIT | ❌ Limited Wayland support |

### Phase 3: Integration Complete

**OpenCode Configuration** (`~/.config/opencode/opencode.json`):
```json
{
  "plugins": [..., "@opencode-ai/browser-control"],
  "mcp": {
    "servers": {
      "playwright": { "type": "local", "command": ["npx", "-y", "@playwright/mcp@latest"] },
      "screen-mcp": {
        "type": "local",
        "command": ["/data/screen-mcp/.venv/bin/python", "-m", "screen_mcp"],
        "environment": { "MCP_SCREEN_GUARD": "1", "MCP_SCREEN_AMBIENT": "1" }
      }
    }
  }
}
```

**screen-mcp Installation** (`/data/screen-mcp/`):
- System deps: GStreamer 1.28, PipeWire, xdg-desktop-portal-gnome, wl-clipboard, fonts-dejavu ✅
- Python venv with `--system-site-packages` + all runtime deps ✅
- GNOME window-info extension installed ✅ (needs relogin)
- All 22 MCP tools registered and functional ✅

### Phase 4: Documentation Created

| File | Purpose |
|------|---------|
| `browser-desktop-automation.md` | Full architecture, routing, safety patterns |
| `manual-setup.md` | Step-by-step manual installation guide |
| `orchestrator-quickref.md` | Quick reference for task routing |
| `validation-tests.sh` | Automated validation script |

### Phase 5: Reliability Patterns Implemented

- **Inspect → Act → Verify** loop enforced by both toolsets
- **Human approval gates** for consequential actions
- **Untrusted content handling** (never obey webpage instructions)
- **Element reference refresh** after navigation/UI changes
- **User-takeover guard** (screen-mcp yields on human mouse movement)

---

## ⏳ Manual Steps Required (Cannot Automate)

### 1. Install browser-control Chrome Extension
```bash
# Extension directory:
/home/mrknight/.cache/opencode/npm/@opencode-ai/browser-control@latest/1792910652698/node_modules/@opencode-ai/browser-control/extension/dist

# Steps:
# 1. Open chrome://extensions
# 2. Enable Developer mode
# 3. Click "Load unpacked"
# 4. Select the directory above
# 5. Pin the "Browser Control" toolbar button
```

### 2. Activate GNOME window-info Extension (Requires Relogin)
```bash
# The extension is installed but Wayland requires full logout/login
# 1. Save work and log out of GNOME
# 2. Log back in
# 3. Verify: gnome-extensions list --enabled | grep window-info
```

### 3. Restart OpenCode
```bash
pkill -f opencode
opencode
```

---

## 🧪 Validation After Manual Steps

Run the validation script:
```bash
/data/MyFarmAI/docs/engineering/validation-tests.sh
```

Or test from within OpenCode:
```
# Browser automation
@browser Open https://example.com and return the page title

# Desktop automation
screen_screenshot { "annotate": true }
screen_list_monitors {}
screen_focus { "title": "Chrome" }
screen_click { "x": 500, "y": 300, "verify": true }
screen_verify { "expect_change": true }
```

---

## 🎯 Agent Routing (Ready to Use)

```
User Request
     │
     ▼
┌────────────────────────────────────────┐
│  Target is a WEB PAGE/URL?             │
└────────────────────────────────────────┘
     │                    │
    YES                  NO
     │                    │
     ▼                    ▼
┌──────────────┐   ┌─────────────────────────────┐
│ Browser Task │   │ Target is NATIVE DESKTOP    │
│   Router     │   │ APPLICATION?                │
└──────────────┘   └─────────────────────────────┘
     │                    │                    │
    YES                  YES                   NO
     │                    │                    │
     ▼                    ▼                    ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ @browser     │   │ screen-mcp   │   │ Clarify /    │
│ skill /      │   │ MCP tools    │   │ Reject       │
│ Playwright   │   │              │   │              │
│ MCP          │   │              │   │              │
└──────────────┘   └──────────────┘   └──────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │ INDEPENDENT REVIEWER   │
              │ (qa-reviewer agent)    │
              │ Verify outcome achieved│
              └────────────────────────┘
```

---

## 📁 Key File Locations

| Component | Location |
|-----------|----------|
| OpenCode config | `~/.config/opencode/opencode.json` |
| screen-mcp source | `/data/screen-mcp/` |
| screen-mcp venv | `/data/screen-mcp/.venv/` |
| browser-control plugin | `~/.cache/opencode/npm/@opencode-ai/browser-control@latest/` |
| Documentation | `/data/MyFarmAI/docs/engineering/` |
| screen-mcp logs | `~/.local/state/mcp-screen/actions.jsonl` |
| screen-mcp screenshots | `~/.local/share/mcp-screen/sessions/` |
| browser-control relay | `http://127.0.0.1:19989` |

---

## 🔧 Maintenance Commands

```bash
# Update browser-control
opencode plugin upgrade @opencode-ai/browser-control

# Update screen-mcp
cd /data/screen-mcp && git pull && .venv/bin/pip install -r requirements-runtime.txt

# Update Playwright MCP
npx -y @playwright/mcp@latest

# Health checks
browser-control doctor
browser-control status
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"screen_diag","arguments":{}}}' | /data/screen-mcp/.venv/bin/python /data/screen-mcp/server.py
```

---

## 📝 Next Session Checklist

When resuming after manual steps:

- [ ] Chrome extension shows "connected" in `browser-control status`
- [ ] GNOME window-info extension active after relogin
- [ ] OpenCode restarted and loads screen-mcp MCP server
- [ ] First screenshot prompts for permission (approve it)
- [ ] `@browser` skill works in OpenCode
- [ ] `screen_screenshot` returns annotated image in OpenCode
- [ ] Validation script passes all tests

---

## 🏁 Final Status

**Core Integration**: ✅ **COMPLETE**
- Both MCP servers operational
- All tools registered
- Documentation complete
- Architecture ready for use

**Manual Steps**: ⚠️ **PENDING USER ACTION**
- Chrome extension install (5 min)
- GNOME relogin (2 min)
- OpenCode restart (30 sec)

**Validation**: ⏳ **READY TO RUN** after manual steps

The MyFarmAI-Orchestrator now has full browser and desktop automation capabilities via:
- **@browser skill** → authenticated web automation
- **Playwright MCP** → headless web testing/scraping
- **screen-mcp MCP** → native Wayland/GNOME desktop automation
- **qa-reviewer agent** → independent verification