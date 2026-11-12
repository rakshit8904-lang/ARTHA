# Artha AI living project context

Last updated: **9 November 2026**. This document is the current project record. Read it with [CHANGELOG](../CHANGELOG.md). Dated handoffs and milestone notes preserve earlier states and should not override this document or later owner instructions.

## Deadline and delivery

**Final team demo and document handover: 11 November 2026, 08:30 IST.** The application will run on the owner's laptop. The approved mobile deliverable is the same responsive website in a phone browser. The owner confirmed **Android**. An installable PWA and native Android/iOS application are future scope.

Development is planned around the owner working solo. Biswa's November 9 contribution has been integrated; this does not revive the obsolete four-person work allocation. A friend's possible assistance remains optional backup. Previously offered working capacity was 7-8 hours per day; this is availability, not logged hours.

## Working rules

- Proactively suggest improvements to user experience, explaining benefits, tradeoffs and scope/deadline impact. Distinguish evidence from hypotheses and obtain approval before implementation.

- Ask when product requirements or financial rules are unclear. Do not invent assumptions.
- Obtain approval before new project decisions or scope; carry already-approved work through verification.
- Prefer concise, readable code and reuse the existing calculation/service layer.
- Financial information is sensitive. Privacy and security are core requirements, but no claim of perfect security or production certification is justified.
- Keep the local workspace and documentation current. Separate verified behavior, proposed features and unresolved decisions.
- Local version control is authorized. No remote push or external sharing is implied.

## Product purpose and audience

Latest clarification: all listed financial categories belong in setup and must also be addable/editable later to tailor the complete experience. The car is an example of general goal/decision support, not a selected first priority. The owner reconfirmed retention of approved parsed records and deletion of original statements. See [questionnaire and personalization requirements](../QUESTIONNAIRE_AND_PERSONALIZATION_REQUIREMENTS.md), which also separates bank/USP research deliverables from customer questions.

The owner confirmed the original demo's full questionnaire and connected financial-decision journey as the product blueprint: one private place to manage finances, learn, understand spending and explore goals such as buying a car in three years. The current tools are a partial realization. See [product vision, prototype gap review and proposed execution plan](../PRODUCT_VISION_AND_EXECUTION_PLAN.md). Implementation phases and financial rules in that plan still require approval; reviewing the blueprint does not authorize all features for the November 11 deadline.

Stage one targets first-time earners and financial beginners in their early, mid and late twenties. People over 30 are a later audience. The core questions are where money goes, whether a move to another city is financially workable, what rental options fit a budget, and how a beginner can learn about saving and investing.

The objective is a working demo, not just mockups. A bank visit to collect savings-scheme/infrastructure information and research to establish three defensible USPs were requested but are not completed. Market-unique claims must not be made without evidence.

## Active workspace and entry point

- Workspace: `D:\Amrita Projects\AiML`.
- Active app: **Artha_AI_privacy**. Develop and run the application here.
- Branch: `integration/biswa-2026-11-09`. The pre-integration `solo/november-demo` branch remains preserved.
- Latest implementation checkpoint at this update: **ce13b99**, expanded monthly summary. Documentation/cleanup commits may follow it.
- Schema: **0013** in source (0012 private goals, 0013 financial profile). The local demo database was backed up (`instance/before-profile-0013-2026-11-10.sqlite3`) and upgraded to 0013 on 10 November; integrity check passed and existing rows were preserved. 0011 added saved goals; 0010 added saved relocation scenarios. Portfolio UI and summary presentation required no new schema.
- Local URL: `http://localhost:5148`; root launcher: `Open Artha Demo.cmd`. Close any older demo servers before relaunching: on 10 November three from 6 and 9 November were still serving the port. Demo data: "Asha's household (fictional demo)" in the rehearsal account, created by `scripts/seed_demo_household.py`. Handover: [HANDOVER_2026-11-10.md](HANDOVER_2026-11-10.md).
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
| Budgets and housing | Individual/family monthly plan, grocery priority, housing-aware fields and commitments | Planning-only items without actual categories show a dash. A new month prefills from the latest earlier plan for review. Blank answers are still saved as ₹0 (not yet "not entered") |
| City comparison | 221-city rent benchmark comparison against entered income | Rent-only, not full city living-cost prediction; undated snapshot/FX and unresolved total-cost meaning |
| Calculators and allocation | Reserve target chosen by user, RD estimate, zero-return savings-goal timing, saved surplus allocation | No universal reserve target or automatic investment split |
| Recurring payments and learning | Heuristic candidates reviewed by user; educational pages | Not confirmed bank subscriptions or personalized financial advice |
| Rental search | User-controlled external search helper for Magicbricks results | No scraping, listing availability verification or live price feed |
| Relocation | Saved/reopened/edited scenarios, monthly and upfront estimates, rent-only city prefill, reset | All other costs explicitly entered; no cash-availability guarantee or LLM agent |
| Financial profile | Ongoing, section-by-section profile: income (frequency, stability), assets (value date, accessible within a week), loans (balance, EMI, rate), periodic bills (real frequency, next due), RDs and reserve. Each answer is amount, zero, doesn't apply or don't know; partial totals labelled; per-section save; "I have none"; shared or private entries | Does not feed the monthly plan, goals or reserve calculator yet; no net-worth figure; three blank rows per save; no physical Android test |
| Saved goals | General goals with a purpose, deadline-first monthly amount (0% return), assigned amount and gap, up to three named ongoing costs (blank amount = not entered), borrowing comparison, total versus goal allocation, phone card layout | Each goal is shared (owners edit) or private (creator and household owners see/edit; only the creator changes visibility; viewers may create private goals). Private goals are excluded from the household total. No delete UI, ledger-tracked progress or priority allocation |
| Manual portfolio | Add/edit holdings, quantity, invested/current values, valuation dates, totals | Manual values only; existing API delete remains, no new UI deletion/JSON edit endpoint, no trades or broker connection |
| Monthly summary | Income/spending difference, categories, unresolved amounts, exclusions, month-specific review links | Unknown/partial coverage; not bank balance or disposable income; no LLM narrative |
| Mobile | Responsive Edge checks at 360/390/1280px for newer flows | Actual Android access and full phone rehearsal still pending |

## Important approved behavior

**Statements:** original files must not remain reopenable. Parsed approved entries remain in the ledger. File-level failures create no ledger entries. Review and explicit approval are required. Unapproved review rows expire after 15 minutes of inactivity or cancellation. Exact re-upload after partial approval/cancellation currently returns the existing import without restoring discarded rows.

**Accounting:** transaction type is separate from category. Purchases and fees count as spending; valid matched purchase refunds reduce spending in the refund month and original purchase category. A refund can match only a purchase debit, and all refunds matched to one purchase cannot exceed its amount; this is checked at review edit, approval and ledger correction (records saved before 9 November were not re-validated). Unclassified credits/debits and unmatched refunds are shown separately. Transfers, settlements, cash withdrawals, investments and loan payments are not ordinary purchase spending. Excluded summary amounts are gross ledger-leg volumes, potentially including both transfer legs and both investment directions. No-data totals are unknown. Classified records do not prove complete coverage.

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
| Private goals + financial profile (10 Nov) | 210 passed, 1 skip, 7 warnings; migration 0011→0013→0011→0013 on a demo-database copy preserved rows; existing goals became shared goals on a scratch database; scratch-server checks at 360px |
| UX batch (9 Nov, late) | 195 passed, 1 skip, 7 warnings; scratch-server checks at 360/1280px for goal cards, plan carry-forward and grouped household page |
| Saved goals (9 Nov, late) | 191 passed, 1 skip, 7 warnings; migration round trip on a demo-database copy; scratch-server browser checks at 360/390/1280px |
| Code-review fixes (9 Nov, evening) | Baseline before changes 168 passed, 1 skip; after 179 passed, 1 skip, 7 warnings (11 new guard tests). No browser or Android check for this change |

Login throttling is in-memory and per process, keyed on the connection address; it is suitable for the single-process laptop demo, not a multi-worker or proxied deployment. Logout does not revoke a copied session cookie (14-day lifetime). The PostgreSQL-only skip remains a gap. Browser emulation is not a physical Android test. Real SMTP/SMS, production load, external authentication, comprehensive accessibility and an independent security assessment remain unverified. Full sensitive histories must not be sent to an LLM by default; no provider integration has been approved here.

Detailed evidence: [integration review](HANDOFF_REVIEW_2026-11-09.md), [relocation note](RELOCATION_DEMO_2026-11-09.md), [portfolio note](PORTFOLIO_DEMO_2026-11-09.md), [summary note](MONTHLY_SUMMARY_DEMO_2026-11-09.md). Latest screenshots/scripts are under workspace `outputs/QA`.

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

A standalone context snapshot for Claude Code is available in [CLAUDE_HANDOFF.md](../CLAUDE_HANDOFF.md), including the owner's vision, requirement inventory and explicitly unvalidated market-gap/USP hypotheses. Use this living context and later instructions to resolve any stale snapshot details.

Keep this file current after approved decisions and completed changes. Append behavior, validation and limitations to `CHANGELOG.md`. Preserve milestone notes as dated evidence. `AGENTS.md` directs future work to these records.

Current cleanup categories: `Project_References` for old requirements; `Development_Handoffs` for historical handoffs; `Review_Tomorrow` for uncertain SETU-Q material; `outputs/QA` for verification artifacts; `outputs/Archive` for non-active comparison copies. Historical source repositories remain in place because moving them can break references. Shared handover ZIP/PDF paths remain stable and dated; they are not automatically refreshed by new development.

Do not share the entire workspace blindly. Exclude databases/backups, credentials, original uploads, sessions, virtual environments and caches. Preserve model artifacts and relevant source/data. Never mistake `.gitignore` for filtering an ordinary folder ZIP.


## 10 November 2026 — Agentic AI and responsive UI implementation addendum

The next development work retains the Flask/Jinja/SQLAlchemy application and migration 0013.
The new build adds provider-neutral OpenAI/Gemini chat adapters, locally routed specialist
agents, and a responsive assistant interface. Household context is opt-in: the default request
sends only the selected month's minimised approved-ledger summary; a separate checkbox allows
the user to send their visible profile entries, goals and manually entered portfolio values.
The context builder applies existing private/shared visibility rules and omits monthly plans
because the blank-as-zero issue remains unresolved.

This is a read-only multi-agent foundation, not an unrestricted autonomous execution system.
No state-changing tools or approval queue are enabled. See
`docs/AGENTIC_AI_AND_UI_IMPLEMENTATION.md` for current scope, setup and next engineering gates.
