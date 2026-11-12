# Artha AI — Product vision, demo gap review and execution plan

**Latest clarification:** read [questionnaire and personalization requirements](QUESTIONNAIRE_AND_PERSONALIZATION_REQUIREMENTS.md). All owner-listed financial topics must be available in setup and later editing, and tailor the broader experience. The car is only an illustration of general decision/goal support, not an approved first implementation priority. Original statements are deleted; approved parsed history persists.

Prepared 9 November 2026 for the owner and Claude Code. Read alongside `CLAUDE_HANDOFF.md`, `AGENTS.md`, `docs/PROJECT_CONTEXT.md` and `CHANGELOG.md`.

## 1. The owner's direction — the standard we must build towards

The owner has confirmed that the original demo's complete journey, questionnaire and deliverables represent the product vision. The current backend and screens are a foundation, not the full realization of that vision.

The intended product is one private place to understand finances, learn money management, see spending, and think through decisions a person might otherwise discuss with a friend—or hesitate to share with anyone. The owner wants an experience users would consider worth paying for. Pricing, payment tiers and demonstrated willingness to pay have not been established.

Examples of the questions the product should help a user answer:

- Where is my money going, and what changed?
- What can I comfortably set aside after my commitments?
- I want a car in three years: what would I need to do?
- Can I afford a move to another city without losing sight of my other goals?
- What changes if my income falls or an unexpected expense occurs?
- What do I need to understand before choosing a saving or investment approach?

The experience should be understandable, respectful and nonjudgmental. It should explain options and consequences, ask about missing information, and preserve the user's control. It must not pretend to know a complete financial situation from one statement.

**Initial audience:** first-time earners and beginners in their twenties. Users over 30 are a later audience. Individual and family obligations both matter. Profiles shown in an old prototype do not automatically expand the approved initial audience.

**Approval status:** the owner approved using the original demo journey as the blueprint and reviewing gaps. This document proposes implementation phases and acceptance criteria; it does not approve every design detail, financial rule, integration or deadline expansion. Claude should obtain approval for a concrete implementation batch before editing application behavior.

## 2. Original artifacts located and review boundaries

The following files were located in `D:\Vishal Work\Downloads` and their HTML/source was inspected:

1. `Artha AI – Personal Finance Management.html`: full personal-finance prototype with eleven navigation areas, a ten-section questionnaire, charts and scenario demonstrations.
2. `Artha AI – Personal Finance Management (1).html`: another same-sized copy located; do not assume it differs or is identical without comparing hashes.
3. `ArthaAI – PC with Questionnaire.html`: earlier income-estimation concept with salary expectations, housing, dependents, goals and investment interests.
4. `ArthaAI – PC Version.html`: additional earlier prototype located; not fully reviewed in this pass.

Related downloads include an onboarding workbook and deliverables PDFs. Their contents have not been audited in this pass. Do not claim every external document has been reconciled. The exact file the owner calls "V2" remains to be confirmed; the full personal-finance prototype is the broadest inspected candidate, not a silently settled version choice.

This is a **source-level journey review**, not a new interactive browser walkthrough. Current app evidence comes from inspected templates/routes, existing milestone records and the current context. No new application tests were run for this document.

### What the prototype actually does

The full prototype has Dashboard, Expenses, Income, Investments, Goals, Loans, Retirement, What-If, Bank Statement, Insights and Profile navigation. It uses fixed demo financial values and browser-side calculations. It explicitly says questionnaire answers are not saved, goals cannot yet be added/edited, and selected statements are not parsed. Its insights are templated, not an implemented LLM service.

The earlier questionnaire has a "Save my answers" button that assembles a summary in the page. That button is not evidence of backend persistence. Its income estimate is a formula, not the current trained transaction classifier.

### Preserve the experience; review the financial rules

Do not copy these prototype constants into production as owner-approved rules:

- Health score 74/100; investment-risk score 68/100.
- Universal 30% savings target or six-month emergency target.
- Approximately 8% assumed goal return, illustrative investment returns or growth assurances.
- Goal-status cutoffs using 40% of available savings.
- City multipliers and a universal 15% income buffer.
- Retirement corpus at 25 times projected annual expenses.
- Claims that owning a home automatically frees money for investments or renting makes home purchase the top priority.

These illustrate intended cards and interactions. Their methodology, evidence, input requirements and wording require decisions before implementation. The approved current reserve calculator lets the user choose their target. Current city comparison uses rent benchmarks only.

## 3. Prototype-to-current-app gap matrix

| Prototype area | Current application | Gap to the intended experience |
| --- | --- | --- |
| Dashboard | Household selection and household page with links; separate summary and planning screens | A coherent personal overview with meaningful next actions, progress and data-completeness cues |
| Questionnaire / Profile | Display-name profile; monthly-plan flow captures scope, city, housing, income and expense commitments | Persistent broader profile, assets/liabilities/goals and contextual follow-up; onboarding that connects to the rest of the app |
| Expenses | Approved ledger, spending aggregation, categories, review, refunds and transfer handling | Connected period comparisons, explainable trends and useful follow-up actions; prototype charts are not live evidence |
| Income | Entered plan income and confirmed ledger income | Clear income-source/stability view and explicit distinction between expected and recorded income; no unsupported income prediction |
| Savings | Reserve/RD/goal calculators and saved allocation | A shared view of commitments, reserve, competing goals and money actually assigned to each |
| Investments | Saved manual holdings and editing, invested/current values and valuation dates | Connected goal funding and educational context; no validated risk scoring, live prices or product recommendations |
| Goals | Stateless amount/saved/contribution calculator returning time to target | Named saved goals, deadline-first planning, priority, edits, progress history and shared-budget feasibility |
| Loans | EMI planning line and ledger loan-payment treatment | Individual loans, principal balances, rates, terms and repayment/affordability scenarios |
| Retirement | No equivalent implemented planning journey identified | Long-horizon scenario flow and explicitly approved assumptions; scope relative to initial audience needs confirmation |
| What-If | Saved relocation scenarios | General income/expense/medical/job-loss scenarios connected to budget and goals |
| Bank Statement | Real supported CSV/Excel staging, review, approval and classification | Supported PDF scope remains unresolved; better journey integration without compromising review or deletion rules |
| Insights | Deterministic monthly summary, learning and separate calculators | Personalized, explainable connections between evidence, decisions and possible next steps; no LLM agent currently implemented |
| City affordability | Dataset rent comparison plus saved relocation | Full living-cost estimates need validated data; rental helper is search, not verified listing recommendations |
| Net worth / financial health | Manual portfolio totals, expense/income summaries | Complete dated assets/liabilities before net worth; no arbitrary composite health score |
| Android | Responsive viewport checks recorded | Actual Android access and full phone rehearsal pending |

The strongest current work is the financial-data foundation and several usable planning tools. The largest product gap is connecting these into a persistent, understandable decision journey. This is more than a visual redesign.

## 4. Proposed connected user journey

This sequence translates the vision into a reviewable design; exact screens and required fields need owner approval.

1. **Welcome and purpose:** explain what Artha helps with and how financial data is handled. Let the user identify the question they want help with.
2. **Understand the situation:** collect relevant profile, household commitments, income, housing and priorities through an editable questionnaire. Explain why sensitive questions matter.
3. **Establish the financial picture:** combine explicitly entered planning data with user-approved transactions. Distinguish estimates from records, unknowns from zeros, and household information from personal information.
4. **Show a useful home view:** present what is known, what needs review, spending/plan differences, selected goals and the next useful step. Avoid filling missing data with impressive-looking demo values.
5. **Explore a decision:** car, move, reserve or another chosen goal. Ask follow-up questions, calculate transparently and compare options.
6. **Save a chosen plan:** preview what will be saved and its effect on allocation; retain inputs and assumptions so the user can revisit the reasoning.
7. **Return and review:** update actual progress, explain changes and let the user revise the plan. A change to one goal must not silently overwrite another or create a transaction.
8. **Learn in context:** explain the terms involved in the user's current decision, with optional deeper learning.

No requirement here means collecting every detail on first login. Required/optional fields, skip behavior and staged onboarding remain design decisions. Personal goal visibility inside a family household is particularly important: current owner/viewer access does not automatically provide a private personal-planning space.

## 5. Questionnaire blueprint from the demo

The full prototype contains these ten sections. Preserve them in the vision inventory, while deciding relevance, field types and privacy before implementation.

| Section | Prototype fields | Implementation questions |
| --- | --- | --- |
| Basic profile | Name, age, city, occupation | Exact age versus age range? Which occupation choices serve stage one? |
| Family | Marital status, dependents, children, parents/dependents | Which details are actually necessary? Avoid counting the same dependent twice |
| Income | Monthly income, other income, income stability | Net take-home or another measure? Frequency and variable income? |
| Expenses | Housing, food, electricity, water, transport, EMI, education, medical, internet, shopping, entertainment, travel, other | Reuse current housing and category semantics; separate recorded spend from future commitments |
| Assets | Bank accounts, cash, property, vehicle, investments, gold | Amount/date/ownership; avoid counting portfolio values twice |
| Liabilities | Home, education, personal and credit-card debt, other EMI | Outstanding balance versus monthly payment; what information is required for comparisons? |
| Investments | Mutual funds, stocks, FD, PPF, gold, property, risk tolerance, return preference | Holdings versus interests; no automatic suitability conclusion from preference alone |
| Goals | Name/type, amount, target year, priority | Exact date, funds already earmarked, competing priorities and visibility |
| Retirement | Current age, intended retirement age, desired income | Current-money versus future-money amounts; initial demo inclusion? |
| Financial risk | Income uncertainty, medical risk, debt burden, reserve | Collect only necessary information; avoid unnecessary health details or unvalidated scores |

Retain the owner's later refinements: grocery detail and priority, owned/rented/family housing, society maintenance, medical/term insurance, school fees, parent support, Wi-Fi/communications, recurring deposits and rainy-day planning. They supersede simplistic prototype defaults.

The earlier prototype's expected salary in five years and investment-interest chips are additional candidate inputs, not confirmed mandatory fields. An aspiration must not be treated as a forecast.

## 6. Flagship proposed journey: "I want a car in three years"

### User experience

The app should help the user turn an intention into a plan they understand. Ask for the target budget/date, already earmarked savings, preferred buying approach, and constraints. Explain why a question is needed. Do not require a loan or assume investment returns.

Use current income and commitments only with clear labels and user review. Ask about gaps. Separate purchase funding from continuing costs such as insurance, fuel, maintenance and parking; the exact fields and estimates require approval.

### Transparent starting calculation

For an explicitly selected no-return baseline:

`remaining target = max(target amount − money already earmarked, 0)`

`required monthly contribution = remaining target / remaining contribution months`

Round monetary schedules consistently and adjust the final contribution as needed. Define deadline boundaries and payment timing before implementing. If a date has passed, income is uncertain or costs are missing, ask for clarification rather than displaying a definitive feasibility verdict.

Illustrative fictional example only: a ₹9,00,000 target, ₹1,80,000 already earmarked and 36 contributions needs ₹20,000 per month without assumed returns. If the user confirms ₹12,000 per month is available for this goal, the gap is ₹8,000 monthly. This does not by itself tell the user what expenses to cut or which investment to buy.

### Options to explore, not instructions to follow

- Change the target cost.
- Change the timeline.
- Change the monthly allocation after reviewing commitments and other goals.
- Compare a financing scenario only if requested and with explicit rate/term/fee inputs.
- Explore how uncertain income or ownership costs affect the plan.

Always show the effect on other goals and reserves when those data are available. Do not count one rupee as funding multiple goals or treat invested assets as immediately available cash. No affordability guarantee follows from a positive modeled surplus.

### Proposed acceptance criteria

- User can create, save, reopen and edit a named goal with target date, amount and earmarked funds.
- Required contribution and assumptions are visible and reproducible by backend calculations.
- Missing information remains visible; zero is not substituted for unknown.
- Competing goals share a reviewed allocation; deficits are explained.
- Changing a scenario does not mutate approved transactions or the current plan until an explicit save action.
- Permissions, concurrent edits and data persistence are tested.
- Progress distinguishes actual contributions, manual updates and projections.

Whether this is the first implementation priority is an owner decision, not yet approved by this document.

## 7. Intelligence, explanations and financial trust

Use existing backend financial services for authoritative numbers. The trained category classifier suggests categories; it is not a personal financial adviser, goal-prediction model or conversational agent.

A guided form with conditional questions may provide the first useful decision journey. Conversational AI is a possible interaction layer, not a prerequisite or an approved provider choice. If an LLM is later approved, constrain it to authorized, minimal data and trusted calculator outputs. It must not invent facts, rates or balances, determine permissions, execute payments, or treat uploaded text as instructions.

Each decision output should explain: what inputs were used, their source/date, the assumptions, the calculation, important missing data, and the effect of changing a value. Stronger claims require stronger evidence. Investment projections must remain scenarios rather than promised returns.

## 8. What could make this worth paying for

The intended value is reduced confusion and a useful repeatable decision process—not merely having many screens. Candidate value pillars are:

1. A coherent view of spending, obligations, savings and goals.
2. Private, nonjudgmental exploration of financial choices.
3. Saved plans that remain useful as circumstances change.
4. Contextual learning that helps the user understand their own decisions.
5. Transparent calculations and clear data controls.

These are product hypotheses. No competitor study, unique-in-market claim, customer conversion evidence or paid price point is established. Validate with target users: can they explain their spending, understand the next step for a goal, trust the explanation and return to update a plan? Interview evidence and willingness to pay should shape later prioritization.

## 9. Proposed implementation sequence

| Phase | Work | Gate before proceeding |
| --- | --- | --- |
| A. Blueprint agreement | Confirm which prototype is authoritative; settle first end-to-end journey and demo scope | Owner approval of precise scope and open questions |
| B. Profile and goal persistence | Reuse current household/monthly-plan services; add only needed profile/goal records and migrations | Approved fields, personal/family visibility, duplicate-source rules and migration design |
| C. Connected home and questionnaire | Editable onboarding, summary of known/missing information, useful links into approved records and plans | No conflicting totals; appropriate empty states; owner approves workflow |
| D. One complete decision journey | Proposed car goal with deadline-first calculation, allocation and save/revisit | Formula, timing, funding and ownership-cost scope agreed; tests pass |
| E. Contextual explanations and scenarios | Explain tradeoffs and learning; extend approved what-if flows | No arbitrary scores/returns; any LLM integration separately approved |
| F. Device rehearsal and package | Laptop/Android walkthrough, persistence/privacy/permissions checks, final documentation and extraction test | Recorded real-device results; known limitations clearly disclosed |
| Later expansion | Loans, retirement, complete assets/net worth, richer charts, validated city costs and other goals | Separate prioritization, financial methodology and data validation |

This is an execution proposal, not a promise to complete the full product by the current deadline. Do not silently cut features the owner considers essential; present the tradeoff and obtain a scope decision.

**Immediate hard deadline remains 11 November 2026 at 08:30 IST.** The approved mobile delivery is responsive web on Android. Native/PWA, public deployment, live bank/broker connections and market-data services are not implied. Choose the feasible demo slice only after approval, preserving the broader vision as the roadmap.

## 10. Security and data boundaries that must survive the redesign

- Original statements are discarded after parsing; approved financial records persist. No user-facing original statement reopening.
- Review and explicit approval remain before records affect confirmed totals. ML suggestions are not approval.
- Relational ledger remains authoritative; graphs are derived analytics.
- Preserve type/category separation, matching/refund safeguards, transfer handling and unresolved totals.
- Enforce household permissions and CSRF server-side. Decide personal-versus-family goal visibility explicitly.
- No hidden cross-user data collection for city models; that idea remains research.
- Avoid financial records/credentials in prompts, logs, screenshots, source packages and analytics.
- No claim of perfect security. Recent tests do not replace a production security assessment.
- New sensitive questionnaire data requires a clear retention/edit/delete design. Account deletion/export and personal-goal sharing controls must not be described as implemented without inspection.

## 11. Current technical checkpoint and validation evidence

Active repository: `Artha_AI_privacy`, branch `integration/biswa-2026-11-09`. Latest observed code commit: `d85c784`, code-review guards; local schema recorded as 0010. Stack: Flask, SQLAlchemy, Alembic, Jinja, CSS/JavaScript; local SQLite demonstration; money stored in integer paise.

The latest recorded full suite is **179 passed, 1 PostgreSQL-only skip, 7 warnings**, after refund/auth/input guards. This is an existing result, not a test run for this plan. Earlier feature browser checks exercised 360/390/1280px; physical Android testing remains pending. Login throttling remains process-local; logout does not revoke a copied session cookie. Consult current context for limitations and verify source before changes.

Useful starting files:

- `app/templates/dashboard.html`, `household.html`: current landing/navigation experience.
- `app/templates/monthly_plan.html`: current questionnaire-like planning flow.
- `app/templates/calculators.html`, `app/households/calculations.py`: existing goal/reserve/RD primitives.
- `app/households/calculator_routes.py`: current stateless calculator flow.
- `app/households/plans.py`: saved allocations and monthly planning behavior.
- `app/templates/relocation.html`, `portfolio.html`, `summary.html`: working pieces to connect, not rebuild blindly.
- `tests/`, `migrations/`: regression and persistence foundation.

No application source or schema was changed for this review/document.

## 12. Decisions Claude must clarify with the owner

Ask in small relevant groups before each phase rather than demanding every answer at once:

1. Is the located full personal-finance HTML the intended final demo blueprint, or is there another V2 artifact?
2. Which full journey must work for the November 11 demo? Is the car-in-three-years example the first priority?
3. Which questionnaire sections are essential now; which are optional or collected later?
4. Should personal goals be private from other household members? What sharing control is expected?
5. Should initial goal planning use a no-return baseline, and are loans/ownership costs required in the first slice?
6. How should goals compete for limited funds: user-assigned amounts, priority order, or another approved rule?
7. Is guided form interaction sufficient initially, or is conversation required? If conversation is required, provider/data handling needs a separate decision.
8. Must loans, retirement, risk scoring and net worth be implemented for this demo, or remain explicitly tracked roadmap items?
9. Are live email/phone authentication and any particular PDF layout mandatory for the demo?
10. What Android connection method is approved for rehearsal? Current localhost binding is laptop-only.

## 13. Instructions to Claude Code

Proactively recommend improvements to the user experience whenever you identify them, including alternatives to the current design. Tell the owner what problem they solve, the expected benefit, tradeoffs and effect on scope/deadline. Distinguish observed problems from hypotheses and get approval before implementation.

Read this plan and `AGENTS.md` first, then the live context/changelog and actual Git status. Preserve work by other tools. The old `CLAUDE_HANDOFF.md` remains useful background but predates this clarified product vision and the latest code-review fixes.

Start by confirming the blueprint artifact and the next approved implementation slice. Present its screens, inputs, financial rules, persistence changes and acceptance criteria for approval. Reuse existing services. Prefer concise maintainable code. Do not let attractive prototype numbers become unexplained rules or substitute synthetic data for working integrations.

Use fictional fixtures and an isolated test database. Test permissions, financial edge cases, persistence and relevant responsive behavior. Update living documentation and dated change history after implementation. Keep a truthful boundary between completed, tested, proposed and unresolved work.

The success criterion is a user who understands their situation and can confidently review a realistic plan—not the number of pages, models or agents in the application.
