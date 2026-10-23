# MyFarmAI — UI/UX Design Brief

**Document ID:** MYFARMAI-UX-001  
**Version:** 1.0  
**Status:** Draft — Owner Review Required  
**Product:** MyFarmAI  
**Platforms:** Web and Android  
**Related documents:** PRD, TRD, APP_FLOW, approved SRS and ADRs

## 1. Purpose

This brief defines the experience goals, design principles, users, key journeys, and design deliverables for MyFarmAI. It gives designers and implementation agents a common product-design direction without replacing approved product requirements.

## 2. Product Overview

MyFarmAI is an AI-assisted agriculture platform intended to help users ask agricultural questions and research relevant information. The product is planned for web and Android, with a FastAPI backend, configured AI inference, and a research pipeline that can return source citations.

The interface must make the product's capabilities, limitations, and evidence understandable. It must not present generated advice as guaranteed agricultural outcomes.

## 3. Design Problem

Agricultural users need to find useful information without navigating confusing technical workflows or having to interpret unexplained AI output. Research results can be incomplete, conflicting, or unavailable. The experience must communicate what the system knows, where information came from, and when a result is partial.

## 4. Design Goals

1. Make asking an agricultural question the clearest primary action.
2. Present answers in readable, structured language.
3. Make sources easy to inspect and distinguish from generated synthesis.
4. Provide predictable loading, empty, partial, offline, and error states.
5. Work well on small screens and varying network conditions.
6. Use accessible interaction patterns and clear visual hierarchy.
7. Maintain consistent behavior between web and Android.
8. Avoid clutter, misleading certainty, and unnecessary configuration.

## 5. Proposed Users

These are initial design hypotheses and require owner validation.

### Farmers
- Need direct, understandable answers.
- May use a mobile device and have limited connectivity.
- Need sources and limitations presented without technical jargon.

### Agricultural students and learners
- Need explanations and supporting references.
- May explore a topic through follow-up questions.

### Agricultural advisors
- Need to review evidence and compare source quality before sharing advice.

The final personas, language priorities, and accessibility needs should be validated with actual users where possible.

## 6. Core Experience Principles

### Trust before decoration
Source provenance, uncertainty, and system status must be clear. Do not use visual polish to imply unsupported accuracy.

### Plain language
Use concise labels, familiar terms, and readable explanations. Explain technical errors in user-oriented language.

### Progressive disclosure
Show the answer and key sources first. Place advanced details and secondary controls behind clear, optional interactions.

### Mobile-first resilience
Design for narrow screens, touch input, slow responses, and interrupted connectivity.

### Consistency
Reuse the same component patterns, state labels, spacing, and interaction rules across screens.

### Accessibility
Use semantic structure, sufficient contrast, visible focus, scalable text, accessible labels, and touch targets appropriate to each platform.

### Honest system feedback
Never show a successful result while a request is still running or has failed. Clearly label partial results.

## 7. Information Architecture

Proposed top-level destinations, subject to approved scope:

- **Home:** Primary entry point and question input.
- **Ask MyFarmAI:** Compose and submit an agricultural question.
- **Answer detail:** Answer, limitations, and source references.
- **Research:** Search synthesis and source list.
- **History:** Previous interactions, only if persistence is approved.
- **Settings:** Approved user preferences.
- **Sign in:** Only if user accounts are approved.

Administration and provider configuration should not be exposed as ordinary user navigation.

## 8. Primary User Journeys

### Journey A — Ask a question
1. Open the app.
2. Find the main question input.
3. Enter a question.
4. Submit it.
5. See a clear processing state.
6. Read the answer and limitations.
7. Inspect sources when available.
8. Ask a follow-up question.

### Journey B — Review research
1. Enter a research query.
2. Start research.
3. See progress and any partial-result indication.
4. Review the synthesized findings.
5. Open a source.
6. Return to the results without losing context where feasible.

### Journey C — Recover from a failure
1. The request fails or connectivity is interrupted.
2. The UI explains the failure in plain language.
3. User input is preserved where safe.
4. Retry is offered only when appropriate.
5. The interface does not imply the operation succeeded.

## 9. Screen Requirements

### Home
- Clear product identity.
- One prominent primary question input.
- Short explanation of what MyFarmAI can help with.
- Example questions only if they are relevant and approved.
- Minimal secondary navigation.

### Question composer
- Readable multi-line input where appropriate.
- Clear submit action and disabled/loading state.
- Input constraints and validation feedback.
- Avoid accidental duplicate submissions.

### Answer view
- Strong hierarchy between answer, limitations, and sources.
- Readable paragraphs and lists.
- Citations visually connected to supporting claims where feasible.
- No fabricated or decorative citations.

### Research results
- Clear research status.
- Synthesized findings separated from source metadata.
- Source title, domain, and available date metadata.
- Clear indicators for unavailable or failed sources.

### Settings
- Only expose approved settings.
- Avoid presenting unsupported model or provider controls.

### Authentication
- Only design sign-in, sign-out, or recovery screens if the account requirement is approved.

## 10. Content and Microcopy

Use clear, calm, non-alarmist language.

Preferred examples:
- “Searching for relevant sources…”
- “Some sources could not be retrieved. This result may be incomplete.”
- “We couldn’t connect to MyFarmAI. Check your connection and try again.”
- “No usable sources were found for this query.”

Avoid:
- “100% accurate.”
- “Guaranteed crop results.”
- “Research completed” when only a subset of sources was processed.
- Raw stack traces or internal service names in user-facing errors.

Agricultural recommendations should communicate uncertainty when evidence is limited and encourage expert advice where the consequences of a decision may be significant.

## 11. Visual Direction

Proposed direction: **calm, modern, trustworthy, agriculture-aware, and practical**.

- Use a restrained natural palette as a starting point, not as a locked brand decision.
- Use neutral backgrounds and strong text contrast.
- Reserve accent colors for primary actions, links, and meaningful states.
- Avoid excessive gradients, glass effects, animated backgrounds, and decorative dashboards.
- Prefer meaningful agricultural imagery only where it improves comprehension.
- Use icons consistently and pair unfamiliar icons with labels.

Brand colors, logo, typography, illustration style, and final art direction require owner approval.

## 12. Responsive and Platform Behavior

### Web
- Support narrow mobile layouts through desktop widths.
- Use responsive content widths and clear keyboard focus.
- Avoid hover-only actions.
- Preserve navigation context when opening a source.

### Android
- Respect platform back navigation.
- Use touch-friendly controls.
- Handle keyboard and system insets.
- Avoid assuming stable network connectivity.
- Use secure platform storage if authentication is approved.

## 13. Accessibility Requirements

- Text contrast should meet WCAG 2.2 AA where applicable.
- Every interactive control must have an accessible name.
- Focus order must be logical.
- Status changes must be announced appropriately to assistive technology.
- Color must not be the only indicator of status.
- Text must remain usable when enlarged.
- Forms must provide clear labels and actionable validation.
- Test with keyboard navigation and screen readers.

## 14. Design Deliverables

1. Validated design brief.
2. Information architecture and navigation map.
3. Low-fidelity wireframes for approved core journeys.
4. High-fidelity web and Android screens.
5. Responsive layouts and platform-specific behavior.
6. UI/UX design system and component inventory.
7. Interactive prototype for key journeys.
8. Accessibility checklist.
9. Developer handoff notes, component states, and spacing/typography tokens.
10. Design QA checklist mapped to the acceptance criteria.

## 15. Usability and Success Measures

Establish a baseline through usability testing before setting numeric targets.

Suggested measures:
- Task completion rate for asking a question.
- Time to find and understand an answer.
- Percentage of users who can locate and open a citation.
- Error recovery success rate.
- User comprehension of partial-result and uncertainty labels.
- Accessibility defects discovered during review.

Do not claim user validation until tests with representative users have actually occurred.

## 16. Constraints and Open Questions

- Confirm target user groups and language/localization priorities.
- Confirm whether account creation and history are in MVP scope.
- Confirm logo, brand identity, and color preferences.
- Confirm supported Android versions and web breakpoints.
- Confirm whether research is user-triggered, automatic, or both.
- Confirm whether low-bandwidth or offline functionality is required.
- Confirm which screens already exist in the repository.

## 17. Design Acceptance Criteria

The design is ready for implementation when:
- The primary user journeys are documented.
- Every approved screen has loading, empty, success, partial, and error states as applicable.
- Web and Android patterns are consistent while respecting platform conventions.
- Source provenance and uncertainty are visible.
- Accessibility checks are documented.
- Components and tokens are specified.
- Open decisions are recorded and assigned for owner review.

**Status:** Draft — Owner Review Required.
