# Artha AI change history

This is the maintained development log. Current scope and future plan: [project context](docs/PROJECT_CONTEXT.md). Entries describe actual implementation, not a claim that every product objective is complete.

## 10 November 2026 — Fictional demo household and handover

- Added `scripts/seed_demo_household.py`: creates "Asha's household (fictional demo)" for an existing account through the real import, review and approval services (approved November statement with a matched refund and one deferred payment), plus October/November plans with allocations, four goals (one private), nine profile entries and one holding. Refuses to run twice.
- Seeded the local demo database for the rehearsal account after a backup (`instance/before-demo-seed-2026-11-10.sqlite3`, integrity ok). Validation: a scratch copy was seeded first and all 15 household pages rendered with HTTP 200; summary figures checked (income ₹52,000, net spending ₹20,069, bills ₹708.33/month).
- Found three separate demo servers from 6 and 9 November still serving port 5148, so stale code could answer requests. Claude was not permitted to stop them; the owner must close them and relaunch.
- Added `docs/HANDOVER_2026-11-10.md`: how to run the demo, walkthrough, feature status, remaining tasks, improvement backlog, roadmap and open decisions.
- Not done: Android rehearsal; source-only package and fresh-extract check.
## 10 November 2026 — Private goals and ongoing financial profile (owner-approved)

- **Private goals (schema 0012):** goals record their creator and are shared or private. Private goals are visible to and editable by their creator and household owners; other members cannot see them. Viewers may create private goals but not shared ones; only the creator can change a goal's visibility, so owners cannot expose someone's private goal. The household total compared with the goal allocation counts shared goals only; private goals get a separate subtotal. Existing goals become shared goals.
- **Financial profile (schema 0013):** new household page link. Five sections (income, assets, loans and debts, periodic bills, RDs and reserve), each saved on its own. Every entry has an explicit answer state (amount known, zero, doesn't apply, don't know yet); blanks are never zero, and totals with unknowns are labelled partial. Periodic amounts carry their real frequency and next due date and are spread per month only for display. "I have none of these" can be recorded by owners. Entries are shared or private with the same rules as goals. Edits use per-entry revisions; a stale edit rejects the whole section save.
- Neither feature changes the monthly plan, allocations, goals' calculations or the ledger.
- Validation: full suite 210 passed, 1 skip, 7 warnings (15 new tests in `tests/test_private_goals.py` and `tests/test_profile.py`). Migration 0011→0013→0011→0013 on a copy of the demo database preserved row counts. Scratch-server browser checks at 360px for the bills section, overview and goal privacy control; no page overflow or console errors.
- Demo database: backed up to `instance/before-profile-0013-2026-11-10.sqlite3` (integrity ok) and upgraded from 0011 to 0013; existing rows preserved. The running demo server must be restarted to load the new code.
- Not done: profile data does not yet feed the monthly plan, reserve calculator or goals; no net-worth view; no physical Android test.
## 9 November 2026 — UX batch: general goals, plan carry-forward, phone layout (owner-approved)

- **General goals:** owner clarified the car is only an example. Goals now record a purpose (purchase, education, family commitment, moving city, reserve, travel, other) and up to three user-named "ongoing costs once reached"; a named cost without an amount stays "not entered". Loan section renamed "Borrowing option". Vehicle-specific labels and placeholder removed. No schema change (inputs JSON).
- **Phone layout:** saved goals show as stacked cards, so the gap is visible at 360px without sideways scrolling.
- **Monthly plan carry-forward:** opening a month with no plan prefills the form from the latest earlier plan in the same household, with a "Started from your YYYY-MM plan" notice. Nothing is saved until Save; saved months and earlier months are not prefilled.
- **Household page:** the 15 tools are grouped under Understand your spending, Plan your month, Decide and track, and Learn.
- **Demo database:** backed up to `instance/before-goals-0011-2026-11-09.sqlite3` (integrity ok) and upgraded to 0011; existing rows preserved. The running demo server must be restarted to load the new code.
- Validation: full suite 195 passed, 1 skip, 7 warnings (4 new tests in `tests/test_plan_prefill.py`; goal tests updated); a later read-compatibility fix was rechecked with 16 targeted tests. Scratch-server browser checks at 360px (goal cards, prefill, grouped page) and 1280px; no page overflow. No physical Android test.
- Still open: the monthly plan still saves blank answers as ₹0 (suggestion 2, deferred by owner choice); no setup-status panel (suggestion 5).
## 9 November 2026 — Saved goals (owner-approved spec)

- Added **Goals** (household page link): named goals with target amount, target month, money already set aside (with an as-of date) and a user-assigned monthly amount. Deadline-first plan with no assumed return: remaining ÷ months from this month (India time) to the month before the target, rounded up to whole rupees, final payment absorbs rounding. Gap and months-at-assigned-amount shown.
- Optional ownership running costs (blank stays "not entered", never zero; not added to the target) and optional loan comparison (reducing-balance EMI rounded up to the paise, interest, total repaid, down payment plus fees and the saving needed for it).
- Goals list compares total assigned with the current month's saved "Savings goals" allocation, or says unknown. Household-wide visibility; owners write, viewers read; stale edits rejected. Never writes transactions or the monthly plan.
- Schema **0011** (`saved_goals`). Validation: 191 passed, 1 skip, 7 warnings (12 new tests in `tests/test_goals.py`); migration upgrade → downgrade → upgrade on a copy of the demo database preserved existing row counts; CSRF-enabled browser save on a scratch server and no page overflow at 360/390/1280px, no console errors. The goals table scrolls sideways on phones.
- Not done: the real demo database is still at 0010 and needs `alembic upgrade head` before Goals opens there. No delete UI, no ledger-tracked contributions, no priority allocation, no private goals. Labels for running costs (fuel, parking) are vehicle-oriented although the owner has since clarified goals must be general. No physical Android test.
## 9 November 2026 — Proactive UX suggestions

- Owner explicitly requested that Claude recommend opportunities to improve user experience. Added the instruction to repository guidance, living context and all three handoff/planning documents, retaining approval before implementation. Documentation only.

## 9 November 2026 — Editable questionnaire and general decision support

- Recorded all owner-listed financial topics as setup and later-entry/edit requirements that tailor the complete experience; added `QUESTIONNAIRE_AND_PERSONALIZATION_REQUIREMENTS.md` with proposed fields, mappings, acceptance criteria and unresolved choices.
- Clarified that the car was illustrative, not a selected implementation priority or the limit of goal support.
- Owner explicitly reconfirmed keeping approved parsed transactions/categories while deleting original statements.
- Separated bank-scheme/infrastructure research and unvalidated USP candidates from customer questionnaire fields. Documentation only; concurrent goal implementation files were left untouched, and no tests or feature completion are claimed.

## 9 November 2026 — Product vision and prototype gap review

- Owner confirmed the original demo and questionnaire as the product blueprint, emphasizing private financial decisions, learning and goal planning worth paying for.
- Located the personal-finance and questionnaire HTML prototypes in Downloads; inspected their source and compared the journey with current templates/services. Exact V2 artifact identity still needs confirmation; no interactive browser walkthrough is claimed.
- Added `PRODUCT_VISION_AND_EXECUTION_PLAN.md` with the eleven-area gap matrix, ten-section questionnaire inventory, proposed car-goal journey, implementation phases, acceptance criteria and decisions needing approval.
- Distinguished demo constants and mock features from approved financial rules and working code. Updated Claude handoff/context pointers. Documentation only; no new test run or application changes.

## 9 November 2026 — Code-review fixes (owner-approved P1 + P2)

- **Refund matching:** a refund can match only a purchase debit, and the refunds matched to one purchase cannot together exceed its amount. Checked at review edit, at approval (so two pending refunds cannot each pass alone) and at ledger correction. Previously over-refunds could push confirmed spending and category actuals below zero. Existing saved records were not re-validated.
- **Login protection:** every registration attempt now counts toward the register limit (previously it never triggered, and "email already exists" was an unthrottled lookup). A successful login clears only that email's failures, not the whole IP bucket. Supabase wrong-password responses (HTTP 400) are now counted and return a uniform 401.
- **Input types:** non-text JSON values for names, institution, description, email and password return 400 instead of a server error.
- **Duplicates on edit:** an edited row is re-checked with the upload rules, including other pending imports and repeats within the same file.
- **Deployment default:** `wsgi.py` defaults `APP_ENV` to `production`, so a deployment that forgets it refuses unsafe settings. The demo launcher already sets `development`; boot was smoke-tested with a scratch database.
- **Docs/tooling:** `beautifulsoup4` added to `requirements-app.txt` (needed by 7 test files); pytest and bs4 were reinstalled into `.venv`. Corrected stale `finance.py` docstring, marked `imports/storage.py` as unused legacy, fixed `docs/testing.md` and `docs/deployment.md`.
- Validation: before changes 168 passed, 1 PostgreSQL-only skip; after 179 passed, 1 skip, 7 warnings (11 new tests in `tests/test_review_guards.py`). No browser, Android or database-migration check (no schema change).
- Not changed: logout still does not revoke a copied session cookie; in-memory per-process throttling; per-request review purge on SQLite.

## 9 November 2026 — Living documentation and workspace organization

- Created `CLAUDE_HANDOFF.md`, a standalone handoff covering owner vision, audience, full requirements, market-gap hypotheses, candidate differentiators, implementation boundaries, review instructions and future plan. Market uniqueness remains unverified. No application change or new test run was made for this document.

- Added the canonical project context, future execution plan and this change history, plus repository instructions to maintain them.
- Recorded the owner's Android phone and approved responsive-web delivery for 11 November at 08:30 IST. Physical-phone rehearsal remains pending.
- Grouped six QA/comparison directories under `outputs/QA` and `outputs/Archive`. Verified SHA-256 values for all 375 moved files. No files were deleted. See `docs/WORKSPACE_MOVES_2026-11-09.json` for reversible old/new paths and hashes.
- Preserved active source, shared deliverables, older research/QA repositories and local sensitive backups in their existing locations. Updated current evidence links and the root guide.
- Documentation/filesystem change only; no new application test run is claimed.

## 9 November 2026 — Expanded monthly summary — ce13b99

- Added category spending, unclassified debits/credits, excluded movements and month-specific review links.
- Exposed unmatched refunds without altering net spending. Kept unknown/partial coverage and explained gross transfer/investment volumes.
- Default month uses India time. No schema change.
- Validation: 22 targeted tests, plus browser checks at 360/390/1280px. No full-suite rerun claimed for this increment.

## 9 November 2026 — Manual portfolio interface — 9becf61

- Added household holdings, totals, valuation dates, add/edit forms and stale-edit protection. Shared validation with the existing JSON create endpoint.
- Manual values only; no trading, live pricing or ledger writes. Existing delete API retained; no new deletion UI or JSON edit endpoint.
- Validation: 166 passed, 1 PostgreSQL-only skip, 7 warnings; mobile/desktop browser create/edit/reopen checks passed. Schema remained 0010.

## 9 November 2026 — Saved relocation scenarios — fcc0f36

- Owner approved saved/reopenable/editable scenarios and city rent-only prefill/reset.
- Added scenario table and migration 0010, explicit monthly/upfront inputs, surplus/shortfall and owner/viewer boundaries.
- Reset does not change saved budgets, transactions or scenarios until the scenario is explicitly saved.
- Validation: 163 passed, 1 skip, 7 warnings; CSRF-enabled browser checks at 360/390/1280px; copied-database upgrade/rollback checks and preserved existing records on upgrade.

## 9 November 2026 — Biswa handoff integration — 2dceb1e

- Integrated city rent explorer, reserve/RD/goal calculators, savings allocations, recurring review, learning/rental-search pages, relocation and portfolio APIs, and connected monthly summary.
- Added migrations 0008/0009. Preserved the original handoff and rollback checkpoints.
- Fixed broken household navigation, summary field mismatch, misleading empty-month coverage, malformed API inputs, allocation concurrency/staleness, test contexts and a destructive test-database override.
- Incoming run: 6 failed, 146 passed, 1 skipped. Reviewed build: 158 passed, 1 skipped, 7 warnings. Responsive viewport checks and database-copy upgrade/rollback passed.
- No LLM agents were present in the handoff or added during integration.

## 7 November 2026 — Teammate package and project report

- Produced the dated 14-page handover PDF and editable Markdown with scope, status, models, QA, limitations and future work.
- Created `Artha_AI_Teammate_Package_2026-11-07.zip` from tracked source, excluding private databases/configuration and caches, with models and manifest included.
- Verified archive integrity/hashes and extracted-package migration, login/health and classifier loading. This dated package predates November 9 development.

## 7 November 2026 — Housing-aware budgets — 8f92ba1

- Added owned/rented/family housing choices, included/excluded rent maintenance, and family-support split without double counting. Migration 0007 preserves old plan values without inventing ownership.
- Validation: 130 passed, 1 skipped, 7 warnings, plus housing browser checks.

## 6 November 2026 — Integrated solo foundation — bac8be8

- Checkpointed privacy-focused CSV/Excel review, local classifier, deferred classification, spending, money flow/transfer confirmation and monthly planning.
- Preserved all four frozen model artifacts and final-test evidence. Fixed request-token/bearer fallback, legacy download access, identity-provider session checks, forwarded-IP handling and development-secret/logging issues.
- Verification recorded at that checkpoint: 125 app tests passed, 1 skipped; 9 shared ML checks passed; clean-checkout migration/model check and fictional browser rehearsal.
- Organized old planning/context files, preserved unclear SETU-Q material for review, deleted only one verified duplicate deck and ten generated caches. Local repositories checkpointed, no new remote push.

## Earlier research and foundations

- Preserved original CPI/RBI/city/HCES and synthetic-profile pipeline, validation, EDA, contracts and historical contributions.
- Earlier documents describing an untrained model, unconnected summary service or four-person task allocation reflect their dates, not current status.
- Refer to the existing Git history and dated handoffs for provenance; do not invent original completion dates or attribute later solo work to old team assignments.


## 10 November 2026 — Agentic AI and responsive UI build

- Added local specialist routing for Financial Analyst, Budget Planner, Goal Planner,
  Relocation Advisor, Investment Educator and Financial Companion.
- Added deterministic read-only financial insight calculations over the authorised monthly
  summary; missing values remain missing and paise are converted explicitly.
- Added authenticated provider-readiness endpoint; it never returns API keys.
- Improved Gemini API key transport by sending the key in the request header rather than URL.
- Added `.env` loading for local development and documented secret setup.
- Expanded assistant UI with specialist roster, provider readiness, conversation reset and
  mobile refinements.
- State-changing agent actions remain disabled pending persistent approval records and
  validated backend executors.
