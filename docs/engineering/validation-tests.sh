#!/usr/bin/env bash
# Browser & Desktop Automation Validation Tests
# Run after: (1) Chrome extension installed, (2) GNOME relogin for window-info extension

set -euo pipefail

echo "=========================================="
echo "MyFarmAI Browser/Desktop Automation Tests"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        ((PASS++))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        ((FAIL++))
    fi
}

# ==========================================
# PRE-REQUISITE CHECKS
# ==========================================
echo "--- Pre-requisite Checks ---"

# Check browser-control relay
if curl -s http://127.0.0.1:19989/health >/dev/null 2>&1 || curl -s http://127.0.0.1:19989 >/dev/null 2>&1; then
    test_result 0 "browser-control relay running at 127.0.0.1:19989"
else
    test_result 1 "browser-control relay running at 127.0.0.1:19989"
fi

# Check screen-mcp server responds (first load may be slow due to ONNX model loading)
if echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | timeout 60 /data/screen-mcp/.venv/bin/python /data/screen-mcp/server.py 2>&1 | grep -q "mcp-screen"; then
    test_result 0 "screen-mcp server responds to initialize"
else
    test_result 1 "screen-mcp server responds to initialize"
fi

# Check Chrome extension connected
BC_STATUS=$(/home/mrknight/.cache/opencode/npm/@opencode-ai/browser-control@latest/1792910652698/node_modules/.bin/browser-control status 2>&1)
if echo "$BC_STATUS" | grep -q "Extension: connected"; then
    test_result 0 "browser-control Chrome extension connected"
else
    test_result 1 "browser-control Chrome extension connected (install extension first)"
fi

# Check GNOME window-info extension
if gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell/Extensions/WindowInfo --method org.gnome.Shell.Extensions.WindowInfo.GetMonitors >/dev/null 2>&1; then
    test_result 0 "GNOME window-info extension active"
else
    test_result 1 "GNOME window-info extension active (relogin required)"
fi

echo ""

# ==========================================
# BROWSER AUTOMATION TESTS
# ==========================================
echo "--- Browser Automation Tests (via browser-control) ---"

# Test 1: Basic navigation
echo "Test: Navigate to example.com"
BC_OUT=$(/home/mrknight/.cache/opencode/npm/@opencode-ai/browser-control@latest/1792910652698/node_modules/.bin/browser-control execute 'await page.goto("https://example.com"); await page.waitForLoadState("networkidle"); return { title: await page.title(), url: page.url() }' 2>&1)
if echo "$BC_OUT" | grep -q "Example Domain"; then
    test_result 0 "Navigate to example.com and get title"
else
    test_result 1 "Navigate to example.com and get title"
    echo "  Output: $BC_OUT"
fi

# Test 2: Click a link
echo "Test: Click 'More information' link"
BC_OUT=$(/home/mrknight/.cache/opencode/npm/@opencode-ai/browser-control@latest/1792910652698/node_modules/.bin/browser-control execute '
await page.goto("https://example.com");
await page.waitForLoadState("networkidle");
await page.click("a[href=\"https://www.iana.org/domains/example\"]");
await page.waitForLoadState("networkidle");
return { title: await page.title(), url: page.url() };
' 2>&1)
if echo "$BC_OUT" | grep -qi "iana"; then
    test_result 0 "Click link and navigate"
else
    test_result 1 "Click link and navigate"
    echo "  Output: $BC_OUT"
fi

# Test 3: Screenshot
echo "Test: Take screenshot"
BC_OUT=$(/home/mrknight/.cache/opencode/npm/@opencode-ai/browser-control@latest/1792910652698/node_modules/.bin/browser-control execute '
await page.goto("https://example.com");
await page.waitForLoadState("networkidle");
return await page.screenshot({ path: "/tmp/test-screenshot.png", fullPage: true });
' 2>&1)
if [ -f /tmp/test-screenshot.png ]; then
    test_result 0 "Take full-page screenshot"
    rm -f /tmp/test-screenshot.png
else
    test_result 1 "Take full-page screenshot"
fi

# Test 4: Form interaction (using a test form)
echo "Test: Fill and submit form"
BC_OUT=$(/home/mrknight/.cache/opencode/npm/@opencode-ai/browser-control@latest/1792910652698/node_modules/.bin/browser-control execute '
await page.goto("https://httpbin.org/forms/post");
await page.waitForLoadState("networkidle");
await page.fill("input[name=\"custname\"]", "Test User");
await page.fill("input[name=\"custtel\"]", "555-1234");
await page.fill("input[name=\"custemail\"]", "test@example.com");
await page.selectOption("select[name=\"size\"]", "large");
await page.check("input[name=\"topping\"][value=\"cheese\"]");
await page.fill("textarea[name=\"comments\"]", "Test comment");
await page.click("input[type=\"submit\"]");
await page.waitForLoadState("networkidle");
return { url: page.url(), content: await page.textContent("body") };
' 2>&1)
if echo "$BC_OUT" | grep -q "Test User"; then
    test_result 0 "Fill and submit form"
else
    test_result 1 "Fill and submit form"
    echo "  Output: $BC_OUT"
fi

echo ""

# ==========================================
# DESKTOP AUTOMATION TESTS (via screen-mcp)
# ==========================================
echo "--- Desktop Automation Tests (via screen-mcp) ---"

run_screen_tool() {
    local tool=$1
    local args=$2
    echo '{"jsonrpc":"2.0","id":'"$3"',"method":"tools/call","params":{"name":"'"$tool"'","arguments":'"$args"'}}' | timeout 60 /data/screen-mcp/.venv/bin/python /data/screen-mcp/server.py 2>&1
}

# Test 1: List monitors
echo "Test: List monitors"
OUT=$(run_screen_tool "screen_list_monitors" "{}" 10)
if echo "$OUT" | grep -q "monitors"; then
    test_result 0 "screen_list_monitors returns monitor info"
else
    test_result 1 "screen_list_monitors returns monitor info"
    echo "  Output: $OUT"
fi

# Test 2: Screenshot with annotation
echo "Test: Screenshot with Set-of-Marks annotation"
OUT=$(run_screen_tool "screen_screenshot" '{"annotate": true}' 11)
if echo "$OUT" | grep -q "image"; then
    test_result 0 "screen_screenshot with annotate=true returns image"
else
    test_result 1 "screen_screenshot with annotate=true returns image"
    echo "  Output: $OUT"
fi

# Test 3: Read screen text (OCR)
echo "Test: Read screen text via OCR"
OUT=$(run_screen_tool "screen_read_text" '{"use_cache": true}' 12)
if echo "$OUT" | grep -q "elements"; then
    test_result 0 "screen_read_text returns OCR elements"
else
    test_result 1 "screen_read_text returns OCR elements"
    echo "  Output: $OUT"
fi

# Test 4: Focus window (try to focus Chrome)
echo "Test: Focus Chrome window"
OUT=$(run_screen_tool "screen_focus" '{"title": "Chrome"}' 13)
if echo "$OUT" | grep -q "focus"; then
    test_result 0 "screen_focus finds Chrome window"
else
    test_result 1 "screen_focus finds Chrome window (may need Chrome running)"
    echo "  Output: $OUT"
fi

# Test 5: Click with verification (harmless click on desktop)
echo "Test: Click with verification"
OUT=$(run_screen_tool "screen_click" '{"x": 100, "y": 100, "verify": true}' 14)
if echo "$OUT" | grep -q "result"; then
    test_result 0 "screen_click with verify executes"
else
    test_result 1 "screen_click with verify executes"
    echo "  Output: $OUT"
fi

# Test 6: Type text
echo "Test: Type text"
OUT=$(run_screen_tool "screen_type" '{"text": "test", "focus": "gnome-terminal"}' 15)
if echo "$OUT" | grep -q "result"; then
    test_result 0 "screen_type executes"
else
    test_result 1 "screen_type executes (needs terminal focused)"
    echo "  Output: $OUT"
fi

# Test 7: Batch actions
echo "Test: Batch actions (screen_do)"
OUT=$(run_screen_tool "screen_do" '{"steps": [{"action": "wait", "ms": 500}]}' 16)
if echo "$OUT" | grep -q "result"; then
    test_result 0 "screen_do executes batch"
else
    test_result 1 "screen_do executes batch"
    echo "  Output: $OUT"
fi

# Test 8: Diagnostics
echo "Test: Diagnostics"
OUT=$(run_screen_tool "screen_diag" '{}' 17)
if echo "$OUT" | grep -q "prereqs"; then
    test_result 0 "screen_diag returns capability matrix"
else
    test_result 1 "screen_diag returns capability matrix"
fi

echo ""

# ==========================================
# INTEGRATION TESTS
# ==========================================
echo "--- Integration Tests ---"

# Test: Browser + Desktop coordination
echo "Test: Cross-app coordination (browser → terminal)"
# This would need a more complex scenario; for now verify both systems work
BC_STATUS=$(/home/mrknight/.cache/opencode/npm/@opencode-ai/browser-control@latest/1792910652698/node_modules/.bin/browser-control status 2>&1)
SM_OUT=$(run_screen_tool "screen_list_monitors" "{}" 18)
if echo "$BC_STATUS" | grep -q "Extension: connected" && echo "$SM_OUT" | grep -q "monitors"; then
    test_result 0 "Both browser and desktop automation systems operational"
else
    test_result 1 "Both browser and desktop automation systems operational"
fi

echo ""
echo "=========================================="
echo "Results: $PASS passed, $FAIL failed"
echo "=========================================="

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${YELLOW}Some tests failed. Check pre-requisites:${NC}"
    echo "  1. Install browser-control Chrome extension"
    echo "  2. Relogin to activate GNOME window-info extension"
    echo "  3. Ensure Chrome and terminal are running"
    exit 1
fi