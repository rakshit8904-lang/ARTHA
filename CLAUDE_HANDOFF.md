# Artha AI — Complete project handoff for Claude Code

**Owner instruction for Claude:** proactively suggest anything that could improve the user experience. Explain the problem, proposed change, expected benefit, tradeoffs and deadline impact. You are encouraged to improve on the existing design, not merely reproduce it. Present suggestions to the owner and obtain approval before implementing them; distinguish tested findings from hypotheses.

**Latest owner clarification:** [questionnaire and personalization requirements](QUESTIONNAIRE_AND_PERSONALIZATION_REQUIREMENTS.md) records all required setup/later-edit topics, flexible goals (not car-specific), and the reconfirmed distinction between persistent parsed records and deleted original statements.

**Read the newer [product vision and execution plan](PRODUCT_VISION_AND_EXECUTION_PLAN.md) first.** The owner has clarified that the original demo's questionnaire and connected decision experience are the blueprint. This handoff is an earlier snapshot: subsequent code-review fixes are recorded in `CHANGELOG.md` and `docs/PROJECT_CONTEXT.md`, including the 179-pass checkpoint. Do not treat the older embedded test counts below as current.

Prepared **9 November 2026**, for the project owner to share with the active project folder. This is a standalone context snapshot, not authorization to implement every idea mentioned below. No private financial records or credentials are included.

## Read this first

You are continuing an existing application, not starting a replacement. Read this file, `AGENTS.md`, `docs/PROJECT_CONTEXT.md` and `CHANGELOG.md`, then inspect the actual source and Git status. If source or later owner instructions differ from this snapshot, report the discrepancy and use the newer verified state. Do not discard existing work because older documents describe a different architecture or team plan.

The owner wants you to review the project and make changes they approve. Ask for the intended changes if they have not specified them. This handoff itself does not approve a rewrite, new provider, deployment, financial assumption, or broader feature scope.

## 1. The idea, vision and intended value

Artha AI is a personal-finance application intended to help a beginner understand their money and make practical plans. It connects spending records, household commitments, saving/investment education, and the affordability of moving to a different city.

The owner's four central questions are:

1. **Where is all my money going?** Convert supported records into reviewed, categorized entries and understandable spending analysis.
2. **Can I afford to live in another city?** Compare available city data with the user's income and explicitly entered costs, including the cost of moving.
3. **If rent is too high, what options could fit my budget?** Eventually connect affordability analysis with suitable rental choices. The current implementation provides search links, not verified listings.
4. **As a first-time earner, how do I learn to save and invest?** Make commitments, reserves, recurring deposits, goals and basic investing concepts understandable without silently imposing one financial formula on everybody.

The intended experience is dynamic and user-guided: when the app is uncertain, it should ask the user or visibly leave the item unresolved. A guess must not quietly become a confirmed financial fact. The owner wants a complete working experience rather than a visual prototype.

### Audience and context

- First stage: first-time earners and financial beginners in their early, middle and late twenties.
- Later stage: users over 30. Do not redefine the first audience to include every possible financial customer.
- Single-person and family planning both matter. Family responsibilities can exist even for a young earner.
- Current implementation uses INR and Indian financial/planning examples, including recurring deposits, society maintenance, parental support, medical and term insurance, and school fees.
- This is an instructor-reviewed AI/ML project with an immediate demo deadline. Four models were compared to satisfy the instructor requirement; do not confuse that comparison with a requirement to use four runtime agents.
- No approved pricing, paid subscription business model, revenue forecast, market size, acquisition strategy or commercial launch date is recorded. A "single/family plan" is a household planning choice, not evidence of paid tiers.

## 2. Market gap and positioning — hypotheses, not verified market research

The owner asked for the best three features/USPs that are absent from the market. **That uniqueness has not been established.** No current competitor audit or user research is included in this handoff. Do not claim "first," "only," or "not available anywhere" in a report or presentation.

The following organizes the owner's existing ideas into testable positioning hypotheses. It does not add approved implementation scope.

| Hypothesized unmet need | Intended Artha response | Evidence still needed |
| --- | --- | --- |
| A beginner needs a next-step explanation after seeing expenses | Connect reviewed transactions to a monthly plan, learning and user-selected goals | Interviews with first-time earners; compare actual competitor workflows |
| A potential move requires more than a rent figure | Separate present expenses from a saved destination scenario, including monthly costs and upfront moving costs | Validate city data and test whether this changes users' decisions |
| Users need useful analysis without an archive of their original statements | Parse, review, discard originals and retain only the necessary approved financial records | Test user trust and understanding; audit the real data lifecycle |
| Family commitments and ambiguous transfers can distort a simplistic spending total | Explicit household commitments, housing rules, transfer confirmation and unresolved totals | Test realistic fictional and consented samples, without claiming universal parsing accuracy |

### Three candidate differentiators to validate

1. **A beginner-focused journey from spending to planning:** reviewed expenses, grocery-first budgeting, household commitments, reserve/RD/goal tools and learning in one flow. The individual features are not claimed to be novel.
2. **A separate, editable relocation scenario:** compare destination rent, enter the remaining costs, estimate monthly surplus/shortfall and upfront costs, then save and revisit the scenario without overwriting the current budget. Verified rental recommendations remain future scope.
3. **Privacy-conscious, user-confirmed money-flow analysis:** discard original statements, retain approved records, and use derived relationships to help identify internal transfers rather than count them as ordinary income or spending. The combination is a positioning hypothesis, not a proven unique invention.

Before publishing competitive claims, define comparable products, verify their current capabilities from primary sources, date the comparison and document overlaps as well as gaps. Ask the owner before turning this research into new product requirements.

## 3. Full requirement inventory from the owner

| Requirement or idea | Meaning and current boundary |
| --- | --- |
| Deliverables, objectives, age group, app features and documentation | Must be explicit in the final handoff, with working/pending distinctions |
| Email and phone access | Original requirement; local email/password works, actual phone/SMS and live delivery remain unresolved for the demo |
| Questionnaire | Capture the user's situation and commitments; do not guess missing financial values |
| Individual and family planning | Both supported planning scopes; not an approved subscription pricing model |
| Groceries as a priority | Milk, fruits, vegetables and other groceries should be visible in planning |
| Other recurring costs | Electricity, transport, personal maintenance, subscriptions, shopping, Wi-Fi, communications and miscellaneous costs |
| Housing | Owned versus rented; maintenance where applicable, rent share and included maintenance; avoid double-counting EMI or family support |
| Family obligations | Pledged support to parents, school fees and household commitments |
| Protection | Medical and term life insurance planning lines; no insurance sales/integration implied |
| Savings and investments | Mutual funds, reserves/rainy-day funds, recurring deposits and learning; no universal allocation or reserve size approved |
| Existing manual records | Analysis was requested; currently supported import layouts/manual entry do not establish handwritten OCR or arbitrary-document support |
| Statement handling | Earlier request to retain statements was explicitly superseded: originals are discarded after parsing; approved entries persist under appropriate records/categories |
| Review | User review before confirmation; unresolved classifications remain visibly unresolved |
| City cost engine | Use existing datasets for now; do not silently use past customer histories or other users' data |
| Moving to a city | Separate editable, saved scenario; rent-only benchmark prefill and reset behavior approved |
| Rental alternatives | Magicbricks-style idea; current helper opens searches, not a listing integration |
| Graph interpretation | Relational ledger is authoritative; graph is a derived analytics layer, not a replacement database |
| Adaptive interaction | Ask when uncertain; model suggestions do not authorize records or financial actions |
| Bank research | Visit a bank and gather savings-scheme/infrastructure information; still open |
| Mobile | Android responsive website for this demo; installable/native app deferred |
| Security | Sensitive financial data requires careful review, isolation, validation and retention boundaries; never promise zero vulnerabilities |

### Why graph analysis was suggested

Represent financial entities as nodes and money movements as directed edges to help understand recurring payments, internal transfers and spending relationships. A statement often exposes only one side; merchant text is not a verified counterparty identity. Matching and identity inference must remain distinguishable from user-confirmed facts. Current transfer matching and derived flow views do not constitute a verified external financial network.

### Privacy-preserving crowd data idea

The owner asked whether other users' data could improve city costs without violating privacy. This was deferred as research, starting with fictional households. No collection permission, consent flow, aggregation threshold, anonymization guarantee or differential-privacy mechanism has been approved or implemented. Do not reactivate this idea implicitly.

## 4. Delivery contract and decisions still required

**Deadline: 11 November 2026, 08:30 IST.** The owner will demonstrate the project and hand the final document to the team. Development is planned solo; a friend is backup, not an assumed delivery dependency. Biswa's handoff has been integrated. Old four-person task allocations are historical.

The approved device direction is the app on the owner's laptop plus the same responsive website on **Android**. Actual Android testing is not complete. Do not describe headless narrow-screen testing as a successful phone demonstration.

The proposed final package should contain current source, setup instructions, appropriate fictional sample inputs, model/evaluation evidence, a demo walkthrough, a clear feature/status report, known limitations and future work. Final packaging/rehearsal is still pending. Do not redistribute the old November 7 ZIP as though it contains November 9 changes.

Ask the owner before settling unresolved requirements: whether live email/phone verification and a specific bank PDF format are mandatory for this demo; whether partial-import retry needs additional UI; and whether proposed LLM agents belong in scope. A future-scope label does not automatically waive an original requirement for the final product.

No new completion percentage is certified by this handoff. The older 70% estimate predates several completed screens. Reassess against explicit scope and observed end-to-end results, not lines of code or passing-test counts alone.

## 5. Instructions for Claude's review and changes

1. Identify the active repository and read Git status before editing. Preserve uncommitted work. Use `Artha_AI_privacy`, not the historical research or candidate copies.
2. Explain findings with file references, severity, reproduction/evidence, user impact and a proposed fix. Distinguish an observed defect from a concern needing testing.
3. Follow the owner's approval rule: clarify unclear requirements and get changes/new decisions approved before implementing them. A context handoff is not blanket approval for all suggested enhancements. Do not repeatedly ask for an already explicit approval.
4. Prefer small, readable fixes, reuse services, and preserve the existing architecture unless an approved change requires otherwise. The owner explicitly prefers 50 clear lines to 200 unnecessary ones.
5. Check financial semantics, ownership permissions, import lifecycle, schema compatibility and saved-data behavior before cosmetic improvements that could hide defects.
6. Test the behavior that changes, including relevant negative cases. Use temporary fictional databases; inspect test configuration before running destructive setup. Never point tests at the demo or a personal database.
7. Do not send statements, full transaction histories, credentials or local databases to an external model/service. Approval to use Claude for code work does not approve sending financial data to a runtime LLM provider.
8. Do not deploy, push remotely, change firewall/network exposure, add paid services or install integrations without the owner's approval. Keep model/provider selection separate from deterministic feature implementation.
9. Update `docs/PROJECT_CONTEXT.md` and `CHANGELOG.md` after completed changes, including validation and remaining limitations. Update this handoff's date/status if regenerating it; keep older evidence dated.
10. Report what changed, why, what was actually checked and what remains unresolved. Never claim all tests or Android passed when only selected tests or emulation ran.

## 6. Repository orientation and setup cautions

All paths in this section are relative to the active repository unless stated otherwise.

| Path | Role |
| --- | --- |
| `app/` | Flask application: auth, households, imports, ledger, integrations, cities, web/API, security, templates and static assets |
| `app/households/` | Monthly planning, relocation and portfolio behavior |
| `app/integrations/ledger_finance.py` | Ledger-to-financial-summary adapter |
| `migrations/`, `alembic.ini` | Database migration chain; recorded local head 0010 |
| `tests/` | Parser, finance, permissions, privacy, persistence, planning and UI-route tests |
| `ml/`, `data/`, `results/`, `reports/`, `src/` | ML/research code, datasets and evidence; inspect provenance before treating artifacts as production inputs |
| `docs/` | Current context, contracts and milestone evidence |
| `requirements-app.txt`, `requirements.txt` | Dependency manifests; inspect before choosing installation scope |
| `.env.example` | Example configuration only; contains placeholder values and a PostgreSQL URL, not the current local SQLite setup |
| `wsgi.py` | App entry point |
| `instance/` | Local databases/backups; private runtime material, excluded from source handoff |
| `legacy/`, older dated progress files | Historical context; not automatically the current implementation contract |

The source machine uses Windows/PowerShell, a `.venv`, and a laptop-only Flask development server at port 5148. Local demonstration uses SQLite and local authentication. Do not assume the copied virtual environment works on another machine. Check dependency versions and environment configuration before running the application. Do not replace the database URL with the example PostgreSQL URL by accident.

Safe initial read-only commands from the active repository:

```powershell
git status --short
git branch --show-current
git log -8 --oneline
Get-Content AGENTS.md
Get-Content docs/PROJECT_CONTEXT.md
Get-Content requirements-app.txt
Get-Content tests/conftest.py
```

For startup on the owner's machine, inspect the workspace's `Open Artha Demo.cmd` and current environment; do not launch duplicate servers or reset the database. For another machine, prepare a fresh local environment and fictional database using the repository's actual migration/configuration code. A startup command alone is not a validated clean-machine setup guide.

### Review priorities

- Cross-household isolation, owner/viewer writes, CSRF and session handling.
- Statement parsing boundaries, original-file retention, legacy download paths, expiry and duplicate/retry behavior.
- Integer-money arithmetic, refund matching, transfer pairs and ambiguous classifications.
- Saved budget/allocation/scenario/portfolio concurrency and persistence.
- City-data provenance, rent-only labels and no invented living-cost totals.
- Android file picker, forms, keyboard, touch targets, scrolling and saved flows.
- Package completeness, secret exclusion and extraction/setup rehearsal.

## 7. Verified implementation context snapshot

The following reproduces the maintained context as of this handoff, so this file remains useful even when read alone. Its detailed validation record is historical evidence, not a new test run performed for this document.

# Artha AI living project context

Last updated: **9 November 2026**. This document is the current project record. Read it with [CHANGELOG](CHANGELOG.md). Dated handoffs and milestone notes preserve earlier states and should not override this document or later owner instructions.

## Deadline and delivery

**Final team demo and document handover: 11 November 2026, 08:30 IST.** The application will run on the owner's laptop. The approved mobile deliverable is the same responsive website in a phone browser. The owner confirmed **Android**. An installable PWA and native Android/iOS application are future scope.

Development is planned around the owner working solo. Biswa's November 9 contribution has been integrated; this does not revive the obsolete four-person work allocation. A friend's possible assistance remains optional backup. Previously offered working capacity was 7-8 hours per day; this is availability, not logged hours.

## Working rules

- Ask when product requirements or financial rules are unclear. Do not invent assumptions.
- Obtain approval before new project decisions or scope; carry already-approved work through verification.
- Prefer concise, readable code and reuse the existing calculation/service layer.
- Financial information is sensitive. Privacy and security are core requirements, but no claim of perfect security or production certification is justified.
- Keep the local workspace and documentation current. Separate verified behavior, proposed features and unresolved decisions.
- Local version control is authorized. No remote push or external sharing is implied.

## Product purpose and audience

Stage one targets first-time earners and financial beginners in their early, mid and late twenties. People over 30 are a later audience. The core questions are where money goes, whether a move to another city is financially workable, what rental options fit a budget, and how a beginner can learn about saving and investing.

The objective is a working demo, not just mockups. A bank visit to collect savings-scheme/infrastructure information and research to establish three defensible USPs were requested but are not completed. Market-unique claims must not be made without evidence.

## Active workspace and entry point

- Workspace: `D:\Amrita Projects\AiML`.
- Active app: **Artha_AI_privacy**. Develop and run the application here.
- Branch: `integration/biswa-2026-11-09`. The pre-integration `solo/november-demo` branch remains preserved.
- Latest implementation checkpoint at this update: **ce13b99**, expanded monthly summary. Documentation/cleanup commits may follow it.
- Schema: **0010**, including saved relocation scenarios. Portfolio UI and summary presentation required no new schema.
- Local URL: `http://localhost:5148`; root launcher: `Open Artha Demo.cmd`.
- The server currently binds to laptop loopback. This URL is not automatically reachable from Android. Demo restarts can require a fresh login because the development signing key changes.
- Earlier `Artha_AI` and `artha_qa_review` folders are historical repositories, not active apps. Do not run or modify them by mistake.

Architecture: Flask modular monolith, SQLAlchemy, Alembic, server-rendered Jinja, CSS and JavaScript. Local SQLite for demonstration. Monetary ledger values use integer paise. PostgreSQL production/concurrency readiness is not fully verified.

## Current feature state

| Area | Working behavior | Boundary or pending work |
| --- | --- | --- |
| Login and access | Local email/password login, households/accounts, owner/viewer checks | Real email delivery, phone/SMS and live identity-provider validation pending |
| Statement imports | Defined CSV and Excel layouts, validation, review, duplicate handling | Arbitrary bank PDF formats and handwritten-record OCR pending/future |
| Privacy lifecycle | New originals discarded after parsing, no original-download route, pending reviews expire/cancel | Approved parsed data persists; legacy originals require separate handling; expiry waits while app is stopped |
| Transaction review | User accepts/changes suggestions or explicitly defers classification | Deferred entries stay separate from confirmed totals |
| Ledger and money flow | Approved records, corrections, matched-refund treatment, derived flow view, user-confirmed transfer pairs | No verified external counterparty network or bank connection |
| Budgets and housing | Individual/family monthly plan, grocery priority, housing-aware fields and commitments | Planning-only items without actual categories show a dash |
| City comparison | 221-city rent benchmark comparison against entered income | Rent-only, not full city living-cost prediction; undated snapshot/FX and unresolved total-cost meaning |
| Calculators and allocation | Reserve target chosen by user, RD estimate, zero-return savings-goal timing, saved surplus allocation | No universal reserve target or automatic investment split |
| Recurring payments and learning | Heuristic candidates reviewed by user; educational pages | Not confirmed bank subscriptions or personalized financial advice |
| Rental search | User-controlled external search helper for Magicbricks results | No scraping, listing availability verification or live price feed |
| Relocation | Saved/reopened/edited scenarios, monthly and upfront estimates, rent-only city prefill, reset | All other costs explicitly entered; no cash-availability guarantee or LLM agent |
| Manual portfolio | Add/edit holdings, quantity, invested/current values, valuation dates, totals | Manual values only; existing API delete remains, no new UI deletion/JSON edit endpoint, no trades or broker connection |
| Monthly summary | Income/spending difference, categories, unresolved amounts, exclusions, month-specific review links | Unknown/partial coverage; not bank balance or disposable income; no LLM narrative |
| Mobile | Responsive Edge checks at 360/390/1280px for newer flows | Actual Android access and full phone rehearsal still pending |

## Important approved behavior

**Statements:** original files must not remain reopenable. Parsed approved entries remain in the ledger. File-level failures create no ledger entries. Review and explicit approval are required. Unapproved review rows expire after 15 minutes of inactivity or cancellation. Exact re-upload after partial approval/cancellation currently returns the existing import without restoring discarded rows.

**Accounting:** transaction type is separate from category. Purchases and fees count as spending; valid matched purchase refunds reduce spending in the refund month and original purchase category. Unclassified credits/debits and unmatched refunds are shown separately. Transfers, settlements, cash withdrawals, investments and loan payments are not ordinary purchase spending. Excluded summary amounts are gross ledger-leg volumes, potentially including both transfer legs and both investment directions. No-data totals are unknown. Classified records do not prove complete coverage.

**Questionnaire:** groceries include milk, fruit, vegetables and other groceries. Planning lines also cover housing, electricity, Wi-Fi/communications, transport, personal care, subscriptions, shopping, medical/term insurance, school fees, parent support, EMI and miscellaneous spending.

**Housing:** owned homes ask maintenance; rent asks the user's share and whether maintenance is included. EMI is entered once separately. For living with family, total family support includes the housing share: INR 5,000 total with INR 2,000 housing becomes INR 2,000 housing plus INR 3,000 other support, not INR 7,000.

**Relocation owner decisions:** save scenarios for later reopening/editing. Selecting a city loads editable rent only; all other costs require explicit user input, including zero when appropriate. Reset restores city rent and clears other financial inputs, without changing the saved scenario until Save is selected. Current budget and ledger are unchanged. Upfront amount is deposit plus moving/setup costs; first-month living costs and a reserve are not included in that upfront figure.

**Portfolio:** manual invested/current amounts and valuation dates. Show mixed valuation dates and explain simple gain/loss limitations. Owners write, viewers read. Stale edits are rejected. No inferred prices or automatically created ledger transactions.

**Privacy-sensitive future ideas:** learning city costs from other users' data is deferred research. Use fictional-household experiments first. There is no current consent, aggregation or differential-privacy implementation, and this work does not authorize collecting other users' records.

## Machine learning and research context

Four classifiers were compared as required by the instructor: Logistic Regression, Linear SVM, Complement Naive Bayes and Random Forest, plus a majority baseline. Fixed synthetic dataset: 539 descriptions, 13 categories, split 375/80/84. Shared train-only word/word-pair TF-IDF produced 950 features. Template families and identical cleaned descriptions remain in one split; merchants may repeat.

Linear SVM was selected before the authorized final test. Validation accuracy 96.25%; final test 80/84, or 95.24%, macro-F1 0.968263. All four candidates and evidence are saved. The app uses a local hash-checked artifact. Results do not establish real bank-statement accuracy. Do not retrain or tune on the final test to improve the reported score.

Earlier research processed CPI, RBI, LivingCost city records, HCES and 10,000 generated profiles. Research output has 10,000 rows, 73 columns and 15 EDA figures. The goal-feasibility target is rule-derived, not an observed outcome or the trained category model. HCES category benchmarks and synthetic-user joins were not claimed without necessary metadata. Original raw research inputs are not all in source ZIPs.

## Validation record and limitations

| Checkpoint | Observed result |
| --- | --- |
| Incoming Biswa package | 6 failures, 146 passes, 1 PostgreSQL-only skip |
| Reviewed integration | 158 passes, 1 skip, 7 warnings |
| Saved relocation | 163 passes, 1 skip, 7 warnings; database upgrade/rollback copies preserved records |
| Portfolio checkpoint | 166 passes, 1 skip, 7 warnings |
| Expanded summary increment | 22 targeted tests passed; no new full-suite claim |
| Newer feature browser checks | 360px, 390px and 1280px; no page overflow or JavaScript errors in exercised flows |

The PostgreSQL-only skip remains a gap. Browser emulation is not a physical Android test. Real SMTP/SMS, production load, external authentication, comprehensive accessibility and an independent security assessment remain unverified. Full sensitive histories must not be sent to an LLM by default; no provider integration has been approved here.

Detailed evidence: [integration review](docs/HANDOFF_REVIEW_2026-11-09.md), [relocation note](docs/RELOCATION_DEMO_2026-11-09.md), [portfolio note](docs/PORTFOLIO_DEMO_2026-11-09.md), [summary note](docs/MONTHLY_SUMMARY_DEMO_2026-11-09.md). Latest screenshots/scripts are under workspace `outputs/QA`.

## Readiness and remaining scope

The **70% complete / 30% remaining** estimate was the pre-relocation scope-weighted baseline. Relocation, portfolio and monthly-summary presentation have since progressed. Do not continue quoting 70% as a fresh assessment, and do not substitute an invented updated percentage. Reassess against the same weighted scope after the real-device rehearsal and unresolved demo requirements are settled.

Biswa proposed Relocation Planner, Investment/Portfolio and Monthly Financial Analyst LLM agents. None is implemented. These remain **unapproved added demo scope**; do not silently treat the deterministic screens as AI agents. Provider/model choice, privacy terms, tool access and evaluation would be separate decisions.

## Future execution plan

1. **Android rehearsal setup:** confirm the phone/browser and connection method. Current localhost binding is laptop-only. A USB/ADB route (if available) or a controlled local-network setup are possible approaches. Do not change network exposure, firewall rules, public hosting or install tools without an approved concrete setup. Do not expose real financial records for a demo.
2. **Full user journey on laptop and Android:** fictional login, household/account, CSV/Excel import, correction and approval, deferred entries, spending and graph, monthly plan/allocation, city comparison, saved relocation/reset, portfolio edit and monthly summary. Check phone keyboard, scrolling, touch targets, file picker, navigation and persistence. Record defects and fix demonstrated blockers.
3. **Scope decisions before final freeze:** whether real email/phone login must work for this demo; any required bank PDF format; whether partial-import retry needs a UI; whether LLM agents are genuinely required. Keep these visible rather than assuming they are waived.
4. **10 November daytime:** resolve rehearsal defects and run appropriate regression/security checks. Verify the active schema, backups and permission boundaries. Recheck the delivered package on extraction.
5. **10 November evening, proposed feature freeze:** prepare final context/report and demo script, fictional sample files, source-only ZIP and rollback checkpoint. Update the feature matrix and completion assessment using observed results. Avoid adding financial rules or agent dependencies at this stage without an explicit decision.
6. **11 November before 08:30 IST:** verify the prepared laptop and Android demo, rehearse timing, and hand over the final document and package. No new feature dependency should be deferred to the final morning.

Later scope includes live bank/broker/market feeds, arbitrary PDFs/OCR, richer graph/recurrence analysis, privacy-preserving cross-user research, market-validated USPs, broader age groups, and PWA/native packaging. The bank visit and current scheme research also remain open.

## Documentation and cleanup policy

Keep this file current after approved decisions and completed changes. Append behavior, validation and limitations to `CHANGELOG.md`. Preserve milestone notes as dated evidence. `AGENTS.md` directs future work to these records.

Current cleanup categories: `Project_References` for old requirements; `Development_Handoffs` for historical handoffs; `Review_Tomorrow` for uncertain SETU-Q material; `outputs/QA` for verification artifacts; `outputs/Archive` for non-active comparison copies. Historical source repositories remain in place because moving them can break references. Shared handover ZIP/PDF paths remain stable and dated; they are not automatically refreshed by new development.

Do not share the entire workspace blindly. Exclude databases/backups, credentials, original uploads, sessions, virtual environments and caches. Preserve model artifacts and relevant source/data. Never mistake `.gitignore` for filtering an ordinary folder ZIP.


## 8. Dated implementation history snapshot

# Artha AI change history

This is the maintained development log. Current scope and future plan: [project context](docs/PROJECT_CONTEXT.md). Entries describe actual implementation, not a claim that every product objective is complete.

## 9 November 2026 — Living documentation and workspace organization

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


## 9. Provenance and handoff limits

Prepared from the owner's conversation requirements, the maintained local context/change history, repository instructions, source-tree inventory and local Git checkpoints. The two referenced early planning chats were consulted as historical context; their team allocations and incomplete states are superseded by later work. This document does not claim an independent fresh security audit, full-suite rerun or competitor-market study.

At preparation, the latest application-code commit was ce13b99; documentation/cleanup checkpoint was 85210e5. Later documentation commits do not change the application behavior. Verify Git history before editing.

If sharing the project folder, exclude instance databases and backups, actual environment secrets, original financial uploads, browser profiles, session data, virtual environments and caches. Git ignore rules do not filter an ordinary folder ZIP. Keep required source, migrations, approved model artifacts and evidence. Sharing this document does not send any files automatically.
