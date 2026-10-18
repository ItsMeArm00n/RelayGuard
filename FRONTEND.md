# Frontend design system

The interface uses native HTML, one active stylesheet and local JavaScript. It requires no frontend build step, remote fonts, animation libraries or CDN requests.

## Files

- `static/index.html`: all original copy, links, form controls and page sections.
- `static/enterprise.css`: the active design system, component styles and responsive rules. CSS layers separate reset, tokens, shell, components, evidence, motion and responsive styling.
- `static/layout.js`: groups existing nodes into the compact workspace and native expandable sections without discarding their content. It also manages optional ledger columns and row visibility.
- `static/experience.js`: transaction tables, chart rendering, metric summaries and investigation content, using the existing API responses.
- `static/simple-experience.js`: concise page labels and expandable investigation details.
- `static/enterprise-motion.js`: progressive section reveals, navigation transitions, disclosure feedback, dialog dismissal, new-payment feedback and replayable brand entrance.
- `static/blue-architecture.svg`: local vector background with folded blue planes and fine routing lines.
- `static/background.js`: decorative desktop pointer response and a pause/resume control under About this workspace. The two background patterns drift over 14- and 18-second cycles. Hidden tabs pause those cycles; reduced-motion preferences disable them. Pointer response is disabled on coarse pointers. Only background transforms change; interface content stays still.
- `static/review-alerts.js`: tracks newly actionable flagged payments, briefly highlights the Review queue tab and announces changes politely to assistive technology. Amber indicators persist for unreviewed or investigation-needed payments within the loaded event window. Opening the queue acknowledges the animation; ordinary rendering and search do not retrigger it. The navigation count retains its existing total-flagged meaning.
- `static/app.js` and `static/explanations.js`: existing API integration and recorded-model explanations.

Older theme files are retained in the source archive for reference and are not loaded by the page.

## Motion rules

Entrance and exit keyframes use only `transform` and `opacity`, with `cubic-bezier(0.16, 1, 0.3, 1)`. Hover colour and border changes use 180 ms transitions. Replay progress uses `scaleX`, without width animation. Scroll reveals use IntersectionObserver, with no per-frame layout polling. Content is visible before enhancement and never depends on completing an animation.

`prefers-reduced-motion: reduce` disables CSS motion and JavaScript animations. Changing that preference cancels running enhancement animations. Native details, form semantics, focus outlines and keyboard row activation remain available.

Activity & replay details is an always-visible section at the top of Payments, with replay controls in its header. Its chart continues to use the latest scored events; it is no longer hidden behind an expandable control. Other supporting sections remain expandable.

Run `node test_frontend_alerts.cjs` to check attention tracking across incoming flags, repeated rendering, investigations, dismissal, reopened reviews, low-risk payments and reset history.

## Verified for this refactor

- Static retention audit: 161 copy segments, 11 form elements, four links and all 51 source IDs retained. Duplicate IDs from the former breadcrumb fallback were resolved.
- Navigation and native disclosure controls, expanded columns, eight-row compact list, full-list toggle and transaction search.
- Keyboard activation of a payment, AI attribution content, manual-payment form and animated dialog close.
- Model results, model comparison, source/runtime content and settings forms without changing saved reviews or retraining.
- Responsive layout at desktop, 620 px and 390 px viewport settings; no page-level horizontal overflow in the checked narrow layouts.
- JavaScript syntax checks and browser console checks.

The design avoids layout-property animation. Actual frame rate depends on the client device; a cross-device performance benchmark has not been performed.
