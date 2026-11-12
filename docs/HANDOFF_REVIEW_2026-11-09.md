# Biswa handoff integration and demo readiness

Reviewed 9 November 2026. Hard delivery deadline: **11 November 2026 at 08:30 IST** for the team demo and final document. The owner approved a **responsive website for laptop and phone browsers**. An installable PWA or native mobile app is future scope.

## Current assessment

**Approximately 70% complete and 30% remaining for the intended responsive demo.** This is a scope-weighted engineering estimate, not a measured fraction of development hours or proof of production readiness. Treat it as roughly 65-75% until the remaining user journeys and physical-phone rehearsal pass. Backend-only features receive partial credit. Passing tests alone does not make a feature usable in the demo.

| Workstream | Weight | Earned | Remaining |
| --- | ---: | ---: | --- |
| Authentication-independent household, import, review, ledger and money flow | 20 | 19 | Final integrated rehearsal and retry/coverage limitations |
| Questionnaire, housing, budgets and savings allocation | 15 | 13 | Full household journeys, UX refinement and consistency checks |
| City, relocation, rental search, education and portfolio planning | 20 | 11 | Relocation and portfolio interfaces, scenario reset/default behavior, edit flow |
| Four-model experiment and category integration | 10 | 10 | Complete within the approved synthetic experiment; no real-data accuracy claim |
| Responsive mobile delivery | 10 | 4 | Initial viewport checks pass; actual phone connectivity, touch/upload and full flows pending |
| Authentication, privacy and security for the demo scope | 10 | 6 | Email/phone scope decision, targeted new-API CSRF tests and remaining regression review |
| Final packaging, documentation and rehearsal | 15 | 7 | Updated final report, portable package and complete device rehearsal |
| Total | 100 | 70 | 30 scope points remain |

This denominator includes the original working-demo objectives and review of the delivered deterministic additions. Biswa's three proposed LLM agents are **not implemented and are not silently added to the approved demo scope**. If the owner requires them for this deadline, both the scope and estimate must be revised. Production hosting/certification and a native app are not included in this demo estimate.

## Received and preserved

Input: `Artha_AI_Handover_Package_2026-11-09.zip` from Downloads. SHA-256: `f8b7211ddcb3b46c9bef15dc35eb6aee3060cfd81bebf13971e7e48a2e83baa7`.

The outer package contains a Markdown handover, PDF, README and nested application ZIP. The nested ZIP had 288 entries. Its unchanged base matches the prior app at `8f92ba1`. The incoming source differs in nine existing files and adds 25 files. After integration corrections, 38 source/test/document files were copied into the active repository before adding this review.

Original incoming material, comparison inventory and an untouched source rollback ZIP are preserved under `outputs/biswa_handoff_2026-11-09`. Local database backup: `instance/before-biswa-2026-11-09.sqlite3`, excluded from Git. No original user data files were deleted or copied into the handoff source. No remote push was performed.

Integration branch: `integration/biswa-2026-11-09`. The prior branch `solo/november-demo` remains available at the pre-handoff checkpoint. Restoring old code after the schema upgrade also requires deliberate database-version handling; do not overwrite a live database with a backup while the app is running.

## What Biswa added

- Shared spending aggregation used by Spend and monthly-plan actuals, preserving purchase/fee/refund treatment.
- A 221-city rent-affordability explorer, using entered take-home income. It deliberately excludes the unresolved total-cost field. It is not full cost-of-living affordability or family/locality pricing.
- User-input emergency reserve, RD and zero-return savings-goal calculators.
- Persistent allocation of monthly-plan surplus to reserve, goals and discretionary spending.
- Heuristic recurring-payment candidates with explicit confirmation/dismissal. At least three distinct months and amounts within 15% of the median are required; this does not prove a subscription.
- A financial learning page.
- An external Google query helper for Magicbricks rentals. No live listings, scraping or availability verification.
- A deterministic relocation API, separating monthly expenses and upfront deposit/moving/setup costs.
- A manual portfolio model and create/list/delete API. No edit endpoint, portfolio screen, live NAV/price feed or trade execution.
- A read-only monthly finance summary connected at startup.
- Migrations 0008 for allocations/recurring decisions and 0009 for portfolio holdings.

The incoming documentation sometimes says rental integration is absent. The code does contain the search helper; live listing integration is absent. The received document correctly says there are no LLM-backed agents. Keep these distinctions in the final presentation.

## Defects found and corrected during integration

1. Household navigation referenced an unqualified learning endpoint and caused HTTP 500 errors. Corrected the blueprint-qualified link.
2. The new summary response did not match the existing summary screen contract. Added compatible keys and exercised the actual connected service through API and HTML routes.
3. Empty months previously reported zero income/spending and `ledger_classified`. They now return unknown monetary totals and unknown coverage. Months with records remain partial because completeness has not been confirmed. Classification completeness cannot establish account coverage.
4. Summary exclusions could be misread as deduplicated transfers or investment contributions. The output now explicitly labels them as gross ledger-leg volumes, including both transfer legs and both directions of investment movement. No unapproved transfer-deduplication formula was introduced.
5. Relocation accepted boolean deposit months and could interpret omitted income/rent as zero. Required explicit income/rent and bounded, non-boolean numeric inputs.
6. Portfolio creation allowed malformed types to raise server errors, excessively large amounts, quantities that could round below storage precision, and silently truncated notes. Added type, size and precision validation.
7. Allocation revision validation was not an atomic update. Saving now uses a database revision condition. Remaining allocation is recomputed against the current plan; overallocated saved choices are flagged rather than silently reset.
8. Out-of-range month values could produce date exceptions. Added a bounded calendar validation error.
9. Two new tests accessed database services outside a Flask context. Fixed their setup without weakening assertions.
10. The general migration test still honored a potentially destructive external database URL despite the new fixture safeguard. It now uses its own temporary SQLite database.
11. Numeric/search controls lacked the common responsive field sizing. Extended the existing input styles and checked phone-sized pages.

## Verification evidence

Initial incoming suite: **6 failed, 146 passed, 1 PostgreSQL-only skip, 7 warnings**. Four failures traced to household navigation; two to test contexts.

After integration corrections: **158 passed, 1 PostgreSQL-only skip, 7 warnings**, in 155.18 seconds. This includes six new integration tests covering portfolio lifecycle and household roles, malformed input, relocation validation, startup registration and real monthly summaries, stale/overallocated plans, and new page permissions. Eleven targeted tests passed before the full regression run.

The Windows application-control policy blocked a DLL in an old temporary dependency directory. Test execution used the already-installed working SQLAlchemy package ahead of temporary pure-Python test dependencies; no security policy was changed.

Migration verification on a disposable copy of the existing database passed `0007 -> 0009 -> 0007 -> 0009`, with original table rows preserved and SQLite integrity/foreign-key checks passing. The active local database was backed up and upgraded to 0009 after candidate verification.

Headless Edge checks passed at **390px and 1280px**: 12 authenticated pages at each width, city comparison and emergency-reserve form submissions, no page-level horizontal overflow and no JavaScript errors. City tables scroll within their own container on narrow screens. Screenshots and machine-readable results are under `outputs/QA/biswa_20261109`.

This is browser emulation, not a physical-phone test, real-email/SMS verification, a clean-machine install, or production PostgreSQL certification. Test helpers used fictional data. Existing PostgreSQL-only concurrency coverage remains skipped. The frozen classifier artifacts were not retrained or retuned during integration.

## Important remaining gaps

- Relocation has an API but no usable complete scenario screen, persistence, city-default integration or reset workflow. Rent-only comparison does not answer the full question “Can I survive in that city?”
- Portfolio has no user-facing create/list/edit workflow. Manual valuation dates must remain visible.
- Summary HTML shows core contract totals and warnings; category/unresolved/excluded details exist in the API but need presentation work for a complete monthly-analysis screen.
- The city dataset has undated FX/extraction context and unresolved total-cost semantics. No family scaling is established.
- Recurring candidates are heuristic. Confirmation is not external subscription verification; re-review and changing historical patterns need further UX work.
- Real phone login/SMS and email verification remain pending. A decision is needed if they must be live for this demo.
- Mobile access from an actual phone is not configured merely by passing viewport tests. The current app binds to laptop loopback. Choose a controlled local-network or approved hosted demo setup, and test actual touch controls, keyboard, upload, navigation and persistence.
- The exact-file retry limitation after a partly approved/cancelled statement remains.
- New API CSRF/session paths should receive targeted negative tests, alongside the existing common request protections.
- Raw original research inputs are not in the source ZIP. Processed research data is included; full research-pipeline regeneration needs original sources.
- The final Nov 11 document and source ZIP must reflect this release, not the Nov 7 package.

## Proposed remaining execution order

These are recommended next steps for owner approval, not completed work or an instruction to add new scope automatically.

**9 November:** finish the relocation browser flow first, then manual portfolio screens/editing, then expose complete monthly-analysis results. Keep financial arithmetic in the tested services. Explicitly settle scenario defaults/reset and any policy questions before implementation.

**10 November daytime:** complete responsive workflows and targeted privacy/permission checks. Rehearse on the actual laptop and phone, including CSV/Excel import, user correction, saved plan, city comparison and planning outputs. Decide and configure the phone connection method before rehearsal.

**10 November evening:** recommended feature freeze. Prepare fictional demo records, final documentation, a source-only ZIP and rollback copies. Perform an extracted-package startup check and a full timed rehearsal. Avoid new financial features after this point unless fixing a demonstrable blocker.

**11 November before 08:30 IST:** open and verify the prepared demo, confirm both devices connect, and hand over the final document/package. No new feature dependency should be scheduled for the final morning.

Recommended immediate next task: complete the relocation screen around the existing calculation API, with explicit editable inputs and clear monthly/upfront separation. Do not start an LLM provider integration before the owner confirms whether agent features belong in this deadline.

Evidence paths beginning with `outputs/` are relative to the workspace root. For current status after this milestone, see [project context](PROJECT_CONTEXT.md).
