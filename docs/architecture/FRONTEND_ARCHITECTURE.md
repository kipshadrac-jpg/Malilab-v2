# Frontend Architecture

**Status:** Accepted frontend delivery direction and component boundaries. Detailed UI/UX specifications remain a separate phase; no frontend code is created.

## 1. Recommendation

Use one responsive server-rendered web frontend served by Django. Deliver semantic HTML for page content and forms, responsive CSS for the mobile-first editorial experience, and small progressive-enhancement JavaScript modules for calculator input updates or other approved interactions. Do not start with a SPA, separate frontend deployment, native mobile app, or audio interface.

This supports Playbook discovery, search landing pages, rich structured reading, and accessible account workflows with low client-side state and a single authorization boundary. Anonymous users may read public published content; persistent personal features require an authenticated, email-verified account. Search indexing remains published-only.

## 2. Information architecture at domain level

Core reader/learner surfaces:

1. **Discovery:** Playbook-led entry, curated Playbook collections, and basic search/filtering if approved UX requires it.
2. **Playbook detail:** scenario, context/assumptions, questions, recommended Modules, experiments, relevant tools, and related Playbooks as present in that editorial revision.
3. **Module detail:** Module description and ordered Lesson collection, related content, and conceptually explainable learning state.
4. **Lesson reader:** structured block renderer, source/related links, Practice and Lab Tool entry points, Notes/highlight interactions when approved.
5. **Practice and Lab Tool:** accessible data-entry, assumption visibility, calculation output, limitations, and a way to bring a result into My Plan where approved.
6. **My Plan:** personal target/timeframe/assumptions/path, relevant scenarios, and revision context.
7. **Notes and Progress:** user's learning references and explainable learning/achievement record.
8. **Account:** minimal account and user-data access/management flows; exact screens TBD.

Staff surfaces are separate in permissions and navigation: content list/editor, source/asset attachment, review queue, version comparison/context, and publish/retire actions. These are administrative workflows, not public reader pages.

This is an architectural surface inventory, not a final navigation tree, screen design, or requirement to provide every surface in a particular menu.

## 3. Presentation component boundaries

- **Site shell:** responsive page frame, typography/spacing/color tokens, navigation and footer; detailed visual system belongs in UI phase.
- **Discovery components:** Playbook card/cover, summary, topic label, basic search/filter controls.
- **Content reader:** typed block renderer, source/related links, version context, contents navigation if approved.
- **Learning components:** Module lesson list, Practice prompt/form, contextual status indicator.
- **Calculator components:** input groups with units/assumption help, server result summary, sensitivity/scenario view only if approved, limitations and methodology references.
- **Personal workspace components:** Notes, plan revision forms, saved result/plan context, Progress/achievement explanation.
- **Editorial components:** structured block editor, relationship selection, sources/assets, review state and preview. A complex WYSIWYG editor is not assumed.
- **Shared primitives:** semantic buttons/links, forms, validation summaries, tables, callouts, alert/warning, pagination, empty/error states.

Components are presentation only. Formula implementation, authorization, content state transitions, and progress rules stay in server domain/application services.

## 4. Content rendering and safety

Render editorial blocks through a known block registry. Encode plain text by default, validate structure on write and read, and permit only approved safe rich content. Treat URLs/assets as validated references. Do not render raw AI-generated or editor-supplied HTML as trusted markup. Tables must retain accessible header relationships. Warning and disclaimer blocks must remain distinguishable and readable on mobile.

## 5. Interactive behavior

Use ordinary forms and server responses as the baseline. Enhance calculator interactions with JS only if it improves the approved experience. The server remains calculation authority; avoid formula duplication between JS and Python. When recalculating interactively, submit a bounded request to a same-origin JSON use case and show loading, validation, stale/error, and result states accessibly. Save to My Plan only through an explicit authenticated user action unless a later UX decision says otherwise.

Notes, Practice, and My Plan use clear save/update confirmation and avoid losing user-entered information on ordinary validation errors. Autosave/offline support is not assumed.

## 6. Client state and assets

Keep durable user state on the server. Browser state may hold transient form state and progressive interaction state; do not treat local storage as authoritative financial-plan storage. Use versioned static assets and optimized responsive image variants if needed. No audio player, speaker control, voice UI, or podcast asset is permitted in initial product scope.

## 7. Accessibility and responsiveness

Design for narrow screens first, readable line length/spacing, keyboard operation, visible focus, semantic landmarks/headings, labeled controls/units, validation announcements, sufficient contrast, and screen-reader-compatible calculation results. A formal accessibility target and testing requirements remain TODO/TO-BE-DEFINED in the UI/testing phases; architecture supports semantic markup but does not claim conformance.

## 8. Alternatives

| Option | Evaluation |
|---|---|
| Django SSR + progressive enhancement | Recommended: content-first, low complexity, same-origin security, fast initial delivery, accessible baseline. |
| SPA + REST backend | Defer: adds API contracts, client routing/state, duplicated form validation, separate build/deploy and testing needs without approved product demand. |
| Hybrid SSR framework separate from Django | Defer: can provide SSR and rich interactions but duplicates stack/runtime and is not justified before actual UX demonstrates need. |
| Native mobile application | Out of scope for initial architecture; product approves a mobile-first web experience, not a native client. |

Revisit only if approved UX requirements show that SSR/progressive enhancement cannot provide the required interaction quality or a separate client is authorized.
