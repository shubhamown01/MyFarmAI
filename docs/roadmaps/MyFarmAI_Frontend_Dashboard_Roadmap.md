# MyFarmAI Frontend Dashboard --- Complete Development Roadmap

**Project:** MyFarmAI\
**Target:** Responsive web application dashboard shown when users first
open the application\
**Project root:** `/data/MyFarmAI`\
**Frontend root:** `/data/MyFarmAI/web`\
**Status:** Design direction approved; implementation and validation
pending

------------------------------------------------------------------------

## 1. Product Goal

Build a real, responsive MyFarmAI application dashboard---not a
marketing landing page. The first screen should help users:

1.  Ask farming questions using the AI assistant.
2.  Access crop, pest/disease, knowledge, and other farming tools.
3.  See essential weather information at a glance and open a detailed
    weather page when they choose.

The interface should remain simple, focused, accessible, and usable on
desktop, tablet, and mobile.

## 2. Approved Dashboard Layout

### 2.1 Left navigation

-   Home
-   AI Assistant
-   Crops
-   Weather
-   Pest & Disease
-   Knowledge
-   Community
-   Settings

Use an active navigation state. On smaller screens, use a drawer or
suitable compact navigation pattern.

### 2.2 Main workspace

-   Welcome header
-   Farming question input
-   Add Image action
-   Take Photo action
-   Voice input action
-   Send button
-   Quick Actions
-   Recent Questions

Controls must have meaningful behavior. Do not represent unimplemented
capabilities as working features.

### 2.3 Right utility panel

-   Compact weather summary
-   One concise farming tip
-   Small shortcuts to useful tools, where those features exist

### 2.4 Compact weather card

Keep the always-visible weather summary limited to:

-   Selected location
-   Current temperature
-   Weather condition and icon
-   Daily high and low
-   `View Full Weather` action

Do not put hourly forecasts, humidity, wind speed, rainfall probability,
and multiple forecast rows in the compact card. Put detailed information
on the Weather page.

Example values in mockups are illustrative only. The application must
use real data or clearly label development/demo data.

## 3. Existing Technology Stack to Preserve

Verify the current repository and installed packages before changing
dependencies.

  Layer                 Current/expected technology      Direction
  --------------------- -------------------------------- --------------------
  Web framework         Next.js 15                       Keep
  UI framework          React 18                         Keep
  Language              TypeScript                       Keep strict typing
  Styling               Tailwind CSS 3.4                 Keep
  Server state          TanStack Query v5                Reuse
  Client state          Zustand                          Reuse
  Unit tests            Jest and React Testing Library   Reuse
  Browser automation    Playwright                       Reuse
  Accessibility tests   axe-core                         Reuse
  Backend               FastAPI                          Preserve
  Database              Existing project configuration   Preserve
  Local services        Existing Docker Compose setup    Preserve

Do not migrate frameworks, replace the backend, add another UI library,
or install another browser automation framework without a documented
reason.

## 4. AI Agent Team

Reuse the existing OpenCode agent configuration wherever
responsibilities match. Do not create duplicate agents before auditing
the current configuration.

  -----------------------------------------------------------------------
  Agent role                          Responsibilities
  ----------------------------------- -----------------------------------
  MyFarmAI Orchestrator               Coordinates phases, delegates work,
                                      enforces acceptance criteria

  Frontend Design Architect           Defines layout, design tokens,
                                      component boundaries, responsive
                                      behavior

  Frontend UI Engineer                Implements visual structure and
                                      reusable UI components

  Frontend Interaction Engineer       Implements navigation, form
                                      behavior, weather navigation, and
                                      supported interactions

  Backend/API Engineer                Verifies API contracts and
                                      integrates existing endpoints

  Testing/QA Agent                    Runs tests, browser scenarios, and
                                      regression checks

  Frontend UX Auditor                 Reviews usability, responsiveness,
                                      visual consistency, and
                                      accessibility

  Security Agent                      Reviews input handling, uploads,
                                      API security, and authentication
                                      boundaries

  Documentation Agent                 Records decisions, changes, setup,
                                      limitations, and verification
                                      results
  -----------------------------------------------------------------------

### Agent execution rules

-   Work sequentially or with carefully scoped tasks; avoid running
    every local-model agent simultaneously.
-   Keep the design architect read-only during specification.
-   Assign each source file a clear owner during implementation.
-   Avoid concurrent edits to the same file unless explicitly
    coordinated.
-   Have the UX auditor report defects and let the responsible
    implementation agent fix them.
-   Require QA to retest every corrected issue.
-   Do not allow agents to bypass the project's change-safety rules.

## 5. Skills

Audit existing skills first. The environment has previously been
reported to contain:

-   `frontend-design`
-   `frontend-ui-engineering`
-   `ui-ux-pro-max`
-   `web-design-guidelines`
-   `vercel-react-best-practices`
-   `webapp-testing`
-   `performance-optimization`

Verify exact installed names and paths before configuring agents. Add
new skills only when a recurring workflow is not adequately covered.

Useful skill coverage includes:

-   Design-system consistency
-   Responsive UI engineering
-   Next.js and React best practices
-   Accessibility and keyboard navigation
-   Browser testing
-   Visual regression review
-   API contract validation
-   Performance optimization
-   Secure upload handling

Skills are reusable procedures; agents are roles that perform work using
those procedures.

## 6. Plugins, MCP Servers, and Development Tools

These categories are different:

-   **Agents:** perform specialized work.
-   **Skills:** define repeatable procedures.
-   **Plugins/MCP servers:** expose external or local capabilities to
    compatible tools.
-   **CLI tools:** execute development workflows.
-   **Libraries:** application dependencies.

Recommended tools to reuse:

  -----------------------------------------------------------------------
  Tool                    Purpose                 Priority
  ----------------------- ----------------------- -----------------------
  OpenCode CLI            Main coding-agent       Essential
                          environment             

  Git                     Version control and     Essential
                          diff review             

  Node.js/npm             Frontend development    Essential
                          and scripts             

  VS Code                 Manual inspection and   Essential
                          debugging               

  Playwright              Browser automation and  Essential
                          end-to-end tests        

  Playwright MCP          Browser control for     Useful
                          compatible agents       

  Browser MCP             Browser inspection if   Useful
                          the installed server    
                          works                   

  Context7 MCP            Framework documentation Useful
                          lookup                  

  Docker Compose          Run existing integrated Essential for
                          services                integration testing

  axe-core                Automated accessibility Essential for
                          checks                  accessibility
                                                  validation

  Lighthouse              Performance and         Useful
                          web-quality diagnostics 

  Browser DevTools        Console, network, and   Essential
                          layout debugging        
  -----------------------------------------------------------------------

Previously inspected MCP configurations included some servers that
failed to connect or were misconfigured. Verify actual status before
relying on any server. Keep the configuration minimal and avoid fixing
unrelated MCPs during dashboard implementation.

## 7. Implementation Roadmap

### Phase 0 --- Repository and environment audit

Tasks:

1.  Confirm project root is `/data/MyFarmAI`.
2.  Inspect Git branch, working tree, modified files, and untracked
    files.
3.  Inspect `web/package.json` and lockfile.
4.  Review frontend directory structure.
5.  Inspect design tokens and existing components.
6.  Inspect API contracts and current routing.
7.  Verify agent and skill configuration.
8.  Verify Playwright and browser availability.
9.  Run baseline checks and document results.

**Known baseline from the latest reported run:**

-   TypeScript: failed with 3 errors in 2 files.
-   Jest: passed, 11 tests in 1 suite.
-   ESLint: passed with no warnings or errors.
-   `next lint` printed a deprecation notice; migration can be
    considered separately.

The TypeScript errors were reported in:

-   `src/components/ui/Card.tsx:58`: ref type mismatch between
    button/div elements.
-   `src/providers.tsx:26` and `src/providers.tsx:29`: `ResolvedMode`
    type not found.

Inspect both files and existing theme definitions before fixing them.

**Exit criteria:** Current state documented, existing changes protected,
baseline failures understood.

### Phase 1 --- Finalize the design system

Define or verify:

-   Primary/secondary greens
-   Neutral backgrounds and borders
-   Typography scale
-   Spacing scale
-   Border radii
-   Card and button variants
-   Input styles
-   Focus, hover, disabled, and error states
-   Light/dark mode behavior
-   Responsive breakpoints
-   Icon sizing and stroke weight

Reuse semantic tokens and components that already exist. Avoid
duplicating UI components.

**Exit criteria:** Consistent visual rules and accessible component
contracts are documented.

### Phase 2 --- Build the application shell

Implement or reuse:

-   App shell
-   Sidebar
-   Top bar/search
-   Main workspace
-   Right utility panel
-   Active navigation states
-   Responsive navigation
-   Loading/error boundaries as appropriate

Suggested conceptual layout:

``` text
┌─────────────────────────────────────────────────────────────┐
│ Logo             Search / Ask anything            Account   │
├───────────────┬──────────────────────────────┬──────────────┤
│ Home          │ Welcome                      │ Weather      │
│ AI Assistant  │                              │ Summary      │
│ Crops         │ AI Question Input            │              │
│ Weather       │ Quick Actions                 │ Farming Tip  │
│ Pest & Disease│ Recent Questions              │ Quick Tools  │
│ Knowledge     │                              │              │
│ Community     │                              │              │
│ Settings      │                              │              │
└───────────────┴──────────────────────────────┴──────────────┘
```

On small screens, the navigation and utility panel must adapt instead of
squeezing the central content.

**Exit criteria:** Application shell works at desktop, tablet, and
mobile sizes.

### Phase 3 --- Implement dashboard components

Recommended order:

1.  Welcome header
2.  Farming question input
3.  Image attachment control
4.  Camera action
5.  Voice-input action
6.  Send button
7.  Quick Actions
8.  Recent Questions
9.  Compact weather card
10. Farming tip
11. Quick Tools

Reuse existing components and folder conventions. Recent questions
should use actual state/data where available, not fabricated history
presented as real.

**Exit criteria:** Components render correctly, have accessible names,
and provide meaningful feedback.

### Phase 4 --- Implement the weather experience

Compact card:

-   Location
-   Current temperature
-   Weather condition
-   High/low
-   View Full Weather action

Detailed Weather page may include:

-   Current conditions
-   Hourly forecast
-   Multi-day forecast
-   Humidity
-   Wind
-   Rain probability
-   Farming-oriented advice

Integration tasks:

1.  Inspect existing FastAPI weather endpoints.
2.  Confirm the response schema.
3.  Reuse the typed API client if available.
4.  Use TanStack Query for fetching and caching.
5.  Add loading, error, and empty states.
6.  Define refresh behavior.
7.  Handle location permissions and unavailable location.
8.  Show freshness timestamps where available.

Do not invent endpoints or assume a weather provider exists. If there is
no provider, use explicitly labeled development fixtures and document
the missing integration.

**Exit criteria:** Compact summary remains visible where appropriate;
detailed weather is available on demand.

### Phase 5 --- Connect the AI assistant

Tasks:

1.  Inspect the current FastAPI API contract.
2.  Identify the supported question/answer endpoint.
3.  Reuse the typed API client.
4.  Implement question submission and validation.
5.  Show loading and error states.
6.  Render the real backend response.
7.  Support conversation history if provided.
8.  Integrate image uploads only where supported.
9.  Connect voice input only where supported.
10. Preserve authentication and authorization requirements.

**Exit criteria:** Supported questions reach the backend and return real
responses; failures are handled clearly.

### Phase 6 --- Implement navigation and quick tools

Verify routes for:

-   Home
-   AI Assistant
-   Crops
-   Weather
-   Pest & Disease
-   Knowledge
-   Community
-   Settings

Quick-tool shortcuts may include Disease Checker, Fertilizer Guide,
Market Prices, and Government Schemes. They must navigate to real
features or clearly identified planned-feature screens.

**Exit criteria:** All visible navigation controls have defined,
predictable behavior.

### Phase 7 --- Responsive design and accessibility

Test representative viewports:

  Category          Example viewport
  ----------------- ------------------
  Small mobile      320 × 640
  Standard mobile   390 × 844
  Large mobile      430 × 932
  Tablet            768 × 1024
  Laptop            1366 × 768
  Desktop           1920 × 1080

Check:

-   Keyboard navigation
-   Visible focus
-   Semantic HTML
-   Accessible labels
-   Screen-reader names for icon buttons
-   Dialog focus management
-   Color contrast
-   Error messages
-   Reduced-motion preferences
-   Horizontal overflow
-   Touch target usability

Use existing Jest/axe-core tests and add Playwright checks for
browser-level behavior.

**Exit criteria:** No critical accessibility regressions, mobile layout
failures, or keyboard traps in tested flows.

### Phase 8 --- Browser automation and visual QA

Workflow:

``` text
Implement component
      ↓
Run typecheck and unit tests
      ↓
Start application
      ↓
Open in Chromium using Playwright
      ↓
Capture screenshots at target sizes
      ↓
Inspect layout, console, and network
      ↓
Run accessibility checks
      ↓
Record reproducible defects
      ↓
Fix defects
      ↓
Repeat relevant tests
```

Minimum browser scenarios:

1.  Application loads.
2.  Home is the initial route.
3.  Navigation opens the expected page.
4.  Question input accepts text.
5.  Empty submission is handled.
6.  Weather card opens detailed weather.
7.  Loading and error states render.
8.  Mobile layout does not overflow.
9.  Controls are keyboard-accessible.
10. No unexpected console errors occur.

Screenshots must come from the running application. A mockup is a visual
reference, not evidence of implementation correctness.

**Exit criteria:** Critical user flows pass and remaining defects are
documented.

### Phase 9 --- Performance, security, and reliability

Performance:

-   Reuse dependencies.
-   Avoid unnecessarily large client components.
-   Optimize images.
-   Prevent duplicate API requests.
-   Use appropriate caching.
-   Avoid unnecessary re-renders.
-   Inspect loading and network behavior.
-   Respect reduced-motion preferences.

Security:

-   Validate user input.
-   Never expose server secrets to client bundles.
-   Enforce authorization on the backend.
-   Validate upload type and size server-side.
-   Avoid rendering untrusted HTML.
-   Avoid leaking stack traces.
-   Protect configuration.
-   Review dependency advisories without automatically applying breaking
    updates.

Reliability:

-   Handle backend unavailability.
-   Handle empty responses.
-   Show clear error states.
-   Retry only when appropriate.
-   Prevent duplicate submissions.
-   Preserve recoverable user input.

**Exit criteria:** No unresolved critical security issues and common
failures do not crash or mislead the user.

### Phase 10 --- Final verification and documentation

Run from the frontend root:

``` bash
cd /data/MyFarmAI/web

npm run typecheck
npm test -- --runInBand
npm run lint
npm run build
```

Run the relevant Playwright suite afterward. All checks must be
evaluated from their actual output; do not mark a check as passed unless
it passed.

Update the project's existing documentation structure with:

-   Dashboard architecture
-   Component responsibilities
-   Design tokens and layout decisions
-   Routes
-   API integrations
-   Environment requirements
-   Test procedures
-   Known limitations
-   Accessibility findings
-   Performance findings
-   Security review
-   Final verification results

**Exit criteria:** TypeScript, tests, lint, build, browser tests, and
documentation satisfy the acceptance criteria.

## 8. Change-Safety Rules

The repository has previously contained modified and untracked files.
Protect them.

Before each implementation phase:

1.  Inspect Git status.
2.  Identify intended files.
3.  Read relevant source and documentation.
4.  Confirm scope.
5.  Avoid unrelated changes.

After implementation:

1.  Inspect the diff.
2.  Check for accidental edits.
3.  Run relevant checks.
4.  Update documentation.
5.  Review results before proceeding.

Never use `git reset --hard`, `git clean`, or blanket restoration
commands to make the working tree appear clean. Do not overwrite
existing configurations without inspecting them.

**Project rule: No code change without documentation.**

## 9. Dependencies and Installation Policy

Do not install more tools until the audit establishes a real need.

-   Keep the current Next.js, React, Tailwind, TypeScript, Jest,
    Playwright, and axe-core setup.
-   Reuse existing agents, skills, MCP servers, and components.
-   Verify MCP connectivity before relying on it.
-   Avoid redundant browser automation or UI libraries.
-   Prefer free/open-source tooling and local execution where practical.
-   Avoid running many local models simultaneously on the available
    hardware.

## 10. Milestones

  Milestone   Deliverable                    Exit condition
  ----------- ------------------------------ ----------------------------------
  M0          Repository/tooling audit       Baseline documented
  M1          TypeScript baseline repaired   Typecheck passes
  M2          Design system finalized        Tokens/components agreed
  M3          Responsive application shell   Layout/navigation work
  M4          Home dashboard                 Primary components render
  M5          Weather experience             Summary and detailed view work
  M6          AI assistant integration       Supported requests reach backend
  M7          Navigation and quick tools     Routes behave correctly
  M8          Accessibility/responsiveness   Targeted checks pass
  M9          Browser QA                     Critical flows pass
  M10         Security/performance review    No unresolved critical issues
  M11         Final build/documentation      Acceptance criteria satisfied

## 11. Immediate Next Steps

Start with a read-only audit. Do not begin by installing more agents,
plugins, or packages.

``` bash
cd /data/MyFarmAI

git status --short

echo
echo "========== FRONTEND SCRIPTS =========="
node -e "console.log(JSON.stringify(require('./web/package.json').scripts, null, 2))"

echo
echo "========== FRONTEND DEPENDENCIES =========="
npm --prefix web ls --depth=0

echo
echo "========== FRONTEND DOCUMENTATION =========="
find docs/frontend -maxdepth 2 -type f 2>/dev/null | sort

echo
echo "========== PLAYWRIGHT =========="
cd /data/MyFarmAI/web
npx playwright --version

echo
echo "========== TYPESCRIPT =========="
npm run typecheck
```

Then:

1.  Inspect and fix the two existing TypeScript problems.
2.  Document the fixes.
3.  Confirm baseline checks.
4.  Specify the component-level dashboard design.
5.  Implement the application shell and dashboard.
6.  Connect supported interactions and existing APIs.
7.  Run browser QA, correct observed defects, and retest.
8.  Complete final verification and documentation.

## 12. Acceptance Checklist

-   [ ] Home is the first screen users see.
-   [ ] Interface matches the approved application-dashboard direction.
-   [ ] Desktop, tablet, and mobile layouts are usable.
-   [ ] Compact weather summary displays only essential information.
-   [ ] Full weather information opens on demand.
-   [ ] Main navigation works.
-   [ ] AI interactions use supported backend APIs.
-   [ ] Loading, empty, and error states are handled.
-   [ ] Image and voice actions are honest about actual capability.
-   [ ] Unit tests pass.
-   [ ] TypeScript passes.
-   [ ] Lint passes.
-   [ ] Production build succeeds.
-   [ ] Playwright scenarios pass.
-   [ ] No unresolved critical accessibility/security issues.
-   [ ] Documentation matches the actual implementation.

------------------------------------------------------------------------

## Final Recommendation

Keep the first screen focused on three priorities:

1.  **Ask MyFarmAI** --- the primary interaction.
2.  **Access farming tools** --- the primary shortcuts.
3.  **Check weather** --- essential information at a glance, with
    details on demand.

Everything else should support these priorities. Build incrementally,
preserve existing work, use the current tooling, and verify the actual
rendered application at each milestone.
