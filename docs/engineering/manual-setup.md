# Manual Setup Steps for Browser & Desktop Automation

These steps **must be completed manually** before validation tests can pass.

---

## 1. Install browser-control Chrome Extension

### Extension Location
```
/home/mrknight/.cache/opencode/npm/@opencode-ai/browser-control@latest/1792910652698/node_modules/@opencode-ai/browser-control/extension/dist
```

### Installation Steps
1. Open Chrome/Chromium
2. Navigate to `chrome://extensions`
3. Enable **Developer mode** (toggle in top-right)
4. Click **Load unpacked**
5. Select the directory above (`.../extension/dist`)
6. Pin the "Browser Control" toolbar button for easy access

### Verify Installation
```bash
/home/mrknight/.cache/opencode/npm/@opencode-ai/browser-control@latest/1792910652698/node_modules/.bin/browser-control status
```
Should show: `Extension: connected`

---

## 2. Activate GNOME window-info Extension (Requires Relogin)

The extension was installed but **Wayland requires a full logout/login** to load new extensions.

### Steps
1. **Save all work** and close applications
2. Log out of GNOME (top-right menu → Power Off/Log Out → Log Out)
3. Log back in
4. Verify:
   ```bash
   gnome-extensions list --enabled | grep window-info
   # Should show: window-info@local
   
   # Or via D-Bus:
   gdbus call --session --dest org.gnome.Shell \
     --object-path /org/gnome/Shell/Extensions/WindowInfo \
     --method org.gnome.Shell.Extensions.WindowInfo.GetMonitors
   ```

### Without Relogin
- screen-mcp will work but with reduced window awareness (AT-SPI fallback only)
- `screen_focus` may not find native Wayland windows
- `screen_list_monitors` window list will be limited

---

## 3. Verify OpenCode Configuration

### Check opencode.json has both MCP servers
```bash
cat ~/.config/opencode/opencode.json | jq '.mcp.servers | keys'
```
Should include: `playwright`, `screen-mcp`, and others

### Restart OpenCode to pick up new MCP server
```bash
# Kill any running OpenCode processes
pkill -f opencode

# Restart OpenCode
opencode
```

---

## 4. Run Validation Tests

```bash
chmod +x /data/MyFarmAI/docs/engineering/validation-tests.sh
/data/MyFarmAI/docs/engineering/validation-tests.sh
```

---

## 5. Test from Within OpenCode

After restarting OpenCode, test the MCP tools directly:

### Browser Control (via @browser skill)
```
@browser Open https://example.com and return the page title
```

### Screen-MCP (via MCP tools)
```
# In OpenCode, use the MCP tool calls:
screen_screenshot { "annotate": true }
screen_list_monitors {}
screen_focus { "title": "Chrome" }
screen_click { "x": 500, "y": 300, "verify": true }
screen_verify { "expect_change": true }
```

---

## 6. Troubleshooting

### browser-control: Extension not connecting
```bash
# Check relay
/home/mrknight/.cache/opencode/npm/@opencode-ai/browser-control@latest/1792910652698/node_modules/.bin/browser-control doctor

# Check relay logs
# Relay runs at http://127.0.0.1:19989
# Logs in ~/.local/share/opencode/browser-control/
```

### screen-mcp: Permission denied on screenshot
- First run will prompt for screen sharing permission via GNOME portal
- Approve the dialog (check "Remember" for future runs)
- Token cached at `~/.config/mcp-screen/token`

### screen-mcp: No module named 'gi'
- Ensure venv was created with `--system-site-packages`:
  ```bash
  cd /data/screen-mcp
  rm -rf .venv
  python3 -m venv --system-site-packages .venv
  .venv/bin/pip install -r requirements-runtime.txt
  ```

### screen-mcp: Portal not reachable
```bash
# Check xdg-desktop-portal-gnome is running
systemctl --user status xdg-desktop-portal-gnome
# Or restart:
systemctl --user restart xdg-desktop-portal-gnome
```

---

## 7. Post-Setup Verification Checklist

- [ ] Chrome extension shows "connected" in browser-control status
- [ ] GNOME window-info extension enabled after relogin
- [ ] OpenCode restarted and loads screen-mcp MCP server
- [ ] First screenshot prompts for permission (approve it)
- [ ] `@browser` skill works in OpenCode
- [ ] `screen_screenshot` returns annotated image in OpenCode
- [ ] Validation script passes all tests

---

## 8. Quick Test Commands

### From terminal (browser-control)
```bash
# Quick navigation test
/home/mrknight/.cache/opencode/npm/@opencode-ai/browser-control@latest/1792910652698/node_modules/.bin/browser-control execute 'await page.goto("https://example.com"); return await page.title()'

# Check extension status
/home/mrknight/.cache/opencode/npm/@opencode-ai/browser-control@latest/1792910652698/node_modules/.bin/browser-control status
```

### From terminal (screen-mcp)
```bash
# Quick diag
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"screen_diag","arguments":{}}}' | /data/screen-mcp/.venv/bin/python /data/screen-mcp/server.py

# Quick screenshot
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"screen_screenshot","arguments":{"annotate":true}}}' | /data/screen-mcp/.venv/bin/python /data/screen-mcp/server.py
```

---

## Notes

- **browser-control**: Uses your real Chrome profile (cookies, logins, extensions preserved)
- **screen-mcp**: Uses PipeWire + xdg-desktop-portal for screen capture; RemoteDesktop portal for input
- Both work on **Wayland + GNOME** (tested on Ubuntu 24.04)
- First screen-mcp run requires one-time screen-sharing consent via GNOME portal