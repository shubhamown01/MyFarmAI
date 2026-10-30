# Automation Reviewer Skill

## Purpose
Independent verification that browser/desktop automation tasks achieved their intended outcome. Reviews evidence, identifies failed/incomplete steps, and certifies completion.

## When to Use
- After any browser or desktop automation task
- Before reporting task completion to user
- When orchestrating multi-step workflows

## Review Criteria
1. **Objective Met**: Does final state match requested outcome?
2. **Evidence Quality**: Screenshots, logs, extracted data support claims?
3. **Step Completeness**: All required sub-tasks executed?
4. **Error Handling**: Failures caught, recovered, or reported?
5. **Safety Compliance**: No unauthorized actions, approvals obtained?

## Verification Methods
- **Visual**: Compare before/after screenshots
- **Functional**: Re-query target state (read text, check URL, verify data)
- **Contract**: Validate against expected outputs (schemas, values)
- **Process**: Confirm inspect→act→verify loop followed

## Tools
- `screen-screenshot` / `@browser screenshot` — Capture evidence
- `screen_read_text` / `@browser extract` — Read current state
- `screen_verify` — Grade last action
- File system reads — Check outputs, logs, downloads
- Browser/network inspection — Verify API calls, storage changes

## Review Protocol
```
1. Receive task specification + success criteria
2. Collect evidence from automation agent (screenshots, logs, outputs)
3. Execute independent verification checks
4. Compare actual vs expected
5. Report: PASS / FAIL / PARTIAL with evidence
6. If FAIL/PARTIAL: specify missing/incorrect steps for rework
```

## Independence Rules
- Does not execute automation actions (read-only verification)
- Uses separate tool invocations from automation agent
- Reports failures honestly — no "pass" without evidence
- Escalates ambiguous cases to human

## Integration
- Invoked by orchestrator after automation agents complete
- Can be called as subagent: `qa-reviewer` or dedicated reviewer agent
- Produces structured verification report for task completion gate

## Example Verification
```
Task: "Fill contact form at example.com/contact and submit"
Evidence needed:
- Screenshot of filled form before submit
- Screenshot of success message after submit
- Network log showing POST to /api/contact
- Extracted confirmation text

Checks:
1. Form fields match input data
2. Submit succeeded (no error toast)
3. Confirmation message present
4. No unexpected redirects/popups
```