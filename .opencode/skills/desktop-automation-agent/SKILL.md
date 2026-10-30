# Desktop Automation Agent Skill

## Purpose
Control native Linux desktop applications on Wayland/GNOME via screen-mcp. Uses PipeWire screen capture, xdg-desktop-portal for input, and optional OCR/OmniParser grounding.

## When to Use
- Interacting with native desktop apps (not web pages)
- System UI interactions (file dialogs, settings, notifications)
- Reading text from any window via OCR
- Clicking/typeing in apps that lack accessibility APIs
- Cross-application workflows

## Tools Available (MCP: screen-mcp)
- `screen_screenshot` — Capture monitor/region with optional numbered marks
- `screen_list_monitors` — List monitors, focused window
- `screen_click` / `screen_move_mouse` — Pointer control
- `screen_type` / `screen_key` / `screen_hotkey` — Keyboard input
- `screen_scroll` / `screen_drag` — Scroll and drag
- `screen_read_text` — OCR text extraction with click coordinates
- `screen_wait_text` — Block until text appears
- `screen_verify` — Grade last action: CONFIRMED/PARTIAL/NO_OP/DIVERGED
- `screen_focus` — Raise/focus window by title/app/pid
- `screen_do` — Batch ordered actions
- `screen_tour` — Visit multiple UI states
- `screen_session` — Record/replay sessions
- `screen_sense` — Frame diff change detection

## Workflow
1. **Inspect**: `screen_screenshot --annotate=true` → analyze labeled image
2. **Act**: `screen_click --x <N> --y <N>` or `screen_type --text "..."` or `screen_hotkey --keys "ctrl+c"`
3. **Verify**: `screen_screenshot` + `screen_verify` → confirm CONFIRMED
4. **Repeat** until task complete

## Key Principles
- **Inspect → Act → Verify** loop mandatory
- Coordinates from annotated screenshot = click coordinates (global screen space)
- One action per screenshot cycle
- User-takeover guard: stops instantly if human moves mouse (STOPPED result)
- Ack guard (MCP_SCREEN_GUARD=1): blocks destructive combos until confirmed
- Ambient sense (MCP_SCREEN_AMBIENT=1): detects UI changes between actions
- Prefer `screen_focus` + `screen_wait_text` for reliable window targeting
- Use `screen_read_selection` for exact text copy (no OCR)

## Integration
- MCP server: `screen-mcp` in opencode.json
- Command: `/data/screen-mcp/.venv/bin/python -m screen_mcp`
- Requires: Wayland + GNOME, PipeWire, xdg-desktop-portal-gnome, GNOME Shell extension `window-info@local`
- Python venv: `/data/screen-mcp/.venv`
- Screenshots saved to `~/.config/mcp-screen/screenshots/`
- Session cache: `~/.config/mcp-screen/`

## Safety Rules
- Never type passwords, 2FA codes, payment details
- Ask before public/irreversible actions (post, send, buy, delete, accept terms)
- Stop on unexpected dialogs, login pages, errors
- Respect user-takeover guard (mouse movement = immediate stop)

## Example Usage
```
screen_screenshot --annotate=true
screen_focus --title "Settings"
screen_click --x 1200 --y 400
screen_type --text "search term"
screen_hotkey --keys "ctrl+f"
screen_verify
```