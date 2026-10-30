#!/usr/bin/env bash
# Validation script for browser and desktop automation integration
# Run after manual setup steps are complete

set -euo pipefail

echo "=== MyFarmAI Automation Integration Validation ==="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }

# Track results
FAILURES=0

# 1. Check browser-control extension
echo "1. Browser Control Extension"
EXT_DIR="/home/mrknight/.cache/opencode/npm/@opencode-ai/browser-control@latest/1792910652698/node_modules/@opencode-ai/browser-control/extension/dist"
if [[ -f "$EXT_DIR/manifest.json" && -f "$EXT_DIR/background.js" ]]; then
    pass "Extension files present at $EXT_DIR"
else
    fail "Extension files missing at $EXT_DIR"
    ((FAILURES++))
fi

# 2. Check browser-control skill
echo ""
echo "2. Browser Control Skill"
SKILL_DIR="/home/mrknight/.config/opencode/skills/browser-control"
if [[ -f "$SKILL_DIR/skill.md" ]]; then
    pass "Skill installed at $SKILL_DIR"
else
    warn "Skill not found at $SKILL_DIR (may be in OpenCode cache)"
fi

# 3. Check screen-mcp system deps
echo ""
echo "3. screen-mcp System Dependencies"
for pkg in python3-gi python3-gi-cairo gir1.2-gstreamer-1.0 gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-libav pipewire pipewire-pulse xdg-desktop-portal-gnome wl-clipboard fonts-dejavu; do
    if dpkg -l | grep -E "^ii\s+$pkg\s" >/dev/null; then
        pass "$pkg installed"
    else
        fail "$pkg missing"
        ((FAILURES++))
    fi
done

# 4. Check screen-mcp Python venv
echo ""
echo "4. screen-mcp Python Environment"
VENV="/data/screen-mcp/.venv"
if [[ -f "$VENV/bin/python" && -f "$VENV/bin/screen_mcp" ]]; then
    pass "Python venv and screen_mcp module present"
    "$VENV/bin/python" -c "import screen_mcp; print('  Module imports OK')" 2>/dev/null && pass "screen_mcp imports successfully" || fail "screen_mcp import failed"
else
    fail "Python venv or screen_mcp missing at $VENV"
    ((FAILURES++))
fi

# 5. Check GNOME Shell extension
echo ""
echo "5. GNOME Shell Extension (window-info@local)"
if gnome-extensions list --enabled 2>/dev/null | grep -q "window-info@local"; then
    pass "Extension enabled"
else
    warn "Extension not yet enabled (requires Wayland re-login)"
fi

# 6. Check D-Bus service (after re-login)
echo ""
echo "6. D-Bus Service (org.gnome.Shell.Extensions.WindowInfo)"
if gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell/Extensions/WindowInfo --method org.gnome.Shell.Extensions.WindowInfo.GetMonitors 2>/dev/null; then
    pass "D-Bus service responding"
else
    warn "D-Bus service not available (requires Wayland re-login)"
fi

# 7. Check MCP server config
echo ""
echo "7. OpenCode MCP Configuration"
if grep -q "screen-mcp" /data/MyFarmAI/opencode.json; then
    pass "screen-mcp MCP server configured in project"
else
    fail "screen-mcp not in /data/MyFarmAI/opencode.json"
    ((FAILURES++))
fi

if grep -q "browser-control" /data/MyFarmAI/opencode.json; then
    pass "browser-control plugin configured in project"
else
    fail "browser-control not in /data/MyFarmAI/opencode.json"
    ((FAILURES++))
fi

# 8. Check skills
echo ""
echo "8. Automation Skills"
for skill in browser-automation-agent desktop-automation-agent automation-reviewer; do
    if [[ -f "/data/MyFarmAI/.opencode/skills/$skill/SKILL.md" ]]; then
        pass "$skill skill created"
    else
        fail "$skill skill missing"
        ((FAILURES++))
    fi
done

# 9. Check orchestrator routing
echo ""
echo "9. Orchestrator Agent Routing"
if grep -q "Automation Agent Routing" /data/MyFarmAI/.opencode/agents/myfarmai-orchestrator.md; then
    pass "Routing rules documented in orchestrator"
else
    fail "Routing rules missing from orchestrator"
    ((FAILURES++))
fi

# Summary
echo ""
echo "=== Validation Summary ==="
if [[ $FAILURES -eq 0 ]]; then
    pass "All critical checks passed"
    echo ""
    echo "Ready for functional testing. Next steps:"
    echo "  - Test @browser with: @browser Open https://example.com and return title"
    echo "  - Test screen-mcp with: screen_screenshot --annotate=true"
    exit 0
else
    fail "$FAILURES critical check(s) failed"
    echo ""
    echo "Resolve failures before functional testing."
    exit 1
fi