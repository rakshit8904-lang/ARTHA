# Artha AI — Questionnaire, ongoing profile and personalized experience

Owner clarification recorded **9 November 2026**. This document supplements `PRODUCT_VISION_AND_EXECUTION_PLAN.md` and `CLAUDE_HANDOFF.md`. It records product requirements, not a claim that all features are implemented.

## 1. The central requirement

The questionnaire must establish the user's financial situation and help tailor the complete experience. It is not a one-time form that becomes irrelevant after signup.

The owner requires all the financial areas listed below to be available during setup **and available to add or update later**. Users may not have every detail ready on day one. A missing answer must not be silently interpreted as zero, no obligation or no interest.

The product should connect what a user earns, spends, supports, owns, owes, saves and wants to achieve. It should help them understand their situation, learn, and privately explore decisions without judgment. The intended value is a coherent experience useful enough that people might choose to pay for it; pricing and willingness to pay remain unvalidated.

**The car example is illustrative only.** Do not build a car-specific product or treat the car journey as the owner's selected first priority. Build toward flexible goals and decisions: a purchase, education, family commitment, moving city, a reserve, travel or another user-defined objective. Exact scope and implementation order require approval.

## 2. Confirmed requirements versus proposed details

Confirmed by the owner:

- Individual and family planning.
- All listed financial categories available in setup and later.
- Grocery priority and explicit milk, fruit and vegetable detail.
- Information should tailor the wider experience, not just fill a profile page.
- Analysis of customers' existing manual records.
- Retain approved parsed transactions/categories; delete original uploaded statements. The owner explicitly reconfirmed this distinction in this turn.
- Bank savings-scheme/infrastructure research and three defensible USPs remain project deliverables.
- Flexible financial decision support; the car is only an example.

The suggested field structures, navigation, timing rules and personalization mappings below are design proposals for review. They must not become arbitrary financial recommendations or unapproved scope expansion.

## 3. Setup and later-editing experience

Proposed flow:

1. Explain the purpose of setup and how records are handled.
2. Choose individual or family scope and clarify whose income/commitments are included.
3. Gather the relevant financial sections in manageable steps.
4. Offer an explicit way to add missing information later; show incomplete areas without shaming the user.
5. Present a review of what the user entered before saving.
6. Make the same information accessible through an ongoing financial-profile/planning area.
7. Ask relevant follow-up questions when a decision needs missing information.
8. On an edit, explain which plans or estimates change; do not silently rewrite historical transactions.

Exact labels, required minimum fields, autosave versus explicit save, and whether drafts persist need approval. The requirement to add details later is confirmed; those implementation mechanics are not.

Useful answer states to consider: known amount, explicit zero, not applicable, unknown and add later. Distinguish a genuinely absent expense from an unanswered question. A plan using incomplete data must visibly say so.

## 4. Complete financial questionnaire inventory

The collection details below are proposals. Preserve every requested topic even if some are deferred from the first delivery slice.

| Section | Required topic coverage | Suggested details to collect | Intended use |
| --- | --- | --- | --- |
| Plan scope | Individual and family | Whose finances, household responsibilities, personal/shared contributions | Show the correct scope and avoid confusing personal with household totals |
| Income and context | Income, city and relevant household circumstances | Take-home amount, frequency, other income, stability; necessary dependents context | Interpret commitments and explore plans without inventing future income |
| Groceries — priority | Milk, fruits, vegetables and other groceries | User's planned amounts; recurring frequency if needed | Make essential grocery provision prominent before optional allocations |
| Utilities | Electricity | Bill amount/frequency, shared contribution if relevant | Regular household commitments |
| Transport | Transportation | Routine commuting/travel costs, user's share | Monthly affordability and relocation planning |
| Personal care | Personal maintenance | User-defined amount and frequency | Reflect routine needs without judging necessity |
| Subscriptions | Recurring subscriptions | Name, amount, billing interval; optional renewal date | Recurring-cost review and optional user-led decisions |
| Shopping | Shopping and flexible purchases | Planned amount, known upcoming purchases | Show tradeoffs without labeling every purchase wasteful |
| Housing | Owned/rented/family housing; society maintenance | Rent share, whether maintenance is included, separate maintenance, family housing contribution | Housing-aware plan without double counting |
| Connectivity | Wi-Fi and communications charges | Broadband, mobile/phone bills and shared contribution | Show distinct commitments while avoiding overlap |
| Family support | Pledged amounts to parents | Amount, frequency and whether included in another family contribution | Protect understood commitments when exploring new goals |
| Education | School fees for family planning | Amount, payment frequency and next payment if relevant | Recognize irregular obligations, not just a smooth monthly average |
| Medical protection | Medical insurance | Premium/frequency and optionally renewal timing | Budget for coverage costs; do not infer suitability or medical history |
| Life protection | Term life insurance | Premium/frequency and optionally renewal timing | Track a distinct commitment; no automatic product recommendation |
| Mutual funds | Existing holdings, ongoing contributions and learning interest | Separate current value, contributions and intended future investments | Connect manual portfolio/planning with education without guaranteeing returns |
| Recurring deposits | Existing/planned RDs and beginner education | Deposit amount, term, explicitly sourced/user-entered rate and scheme terms | Explain deposits, interest and liquidity; calculate using disclosed conventions |
| Rainy-day reserve | Emergency fund and desired protection | Current earmarked accessible reserve, selected essential costs, chosen coverage duration | Explain target/gap and explore contributions; no universal amount imposed |
| Miscellaneous | Unlisted or irregular spending | Description, amount, frequency | Capture genuine omitted costs without hiding the reserve as ordinary spending |
| Goals and decisions | Any user-defined objective | Name, desired outcome, target amount/date if applicable, earmarked funds, priority | General planning and follow-up, not only vehicle purchases |
| Existing records | Manual records and supported statements | Record format, period, account/scope and user review | Establish actual spending/income and identify incomplete coverage |

Additional asset, liability, risk and retirement topics from the original demo remain in the broader vision document. This inventory supplements them rather than silently removing them.

### Grocery priority must be meaningful

The owner explicitly gives groceries priority. The UI should make grocery commitments easy to see and account for before presenting optional spending/saving choices. Do not invent fixed milk/fruit/vegetable allowances or assume every user's needs are identical. The exact treatment of a budget shortfall needs agreement; software must not silently cut food spending to fund a goal.

### Avoid overlap and double counting

- Groceries are one total assembled from subitems, not a second charge added on top of milk/fruit/vegetable amounts.
- Included society maintenance must not be added to rent again.
- Existing rule: family support that includes housing is split, not summed twice.
- An insurance premium entered in setup and later observed as a transaction is planned versus actual, not two obligations.
- Mutual-fund/RD contributions are allocations or investment movements, not automatically ordinary consumption expenses.
- A reserve is earmarked money; do not bury its balance or contribution under miscellaneous spending.
- A monthly equivalent of school fees helps planning but does not replace the actual payment schedule.
- Portfolio assets and funds assigned to goals must not inflate available resources through duplicate counting.

## 5. How answers should tailor the experience

These are proposed behavior mappings for approval, not claims of current implementation.

| User information | Appropriate adaptation | What must not be inferred |
| --- | --- | --- |
| Individual/family scope | Relevant commitments and clearly labeled totals | Every household member may see personal goals |
| Owned/rented/family housing | Relevant housing questions and calculations | An owner has no housing costs, or every renter wants to buy |
| Parent support/school fees | Include known commitments in goal affordability | Those commitments can be reduced without asking |
| Groceries and essential bills | Show the user's baseline needs | A universal essential-spend allowance |
| Income stability | Ask about uncertainty when exploring future plans | Guaranteed future income or automatic risk tolerance |
| RD or mutual-fund interest | Relevant plain-language learning and optional calculators | Permission to recommend, buy or assume returns |
| Reserve information | Explain an explicitly chosen target and funding gap | A mandatory three/six/twelve-month rule |
| Reviewed records | Ground summaries and comparisons in approved transactions | Complete finances or bank balance from incomplete imports |
| A named goal | Ask relevant follow-ups and compare feasible input scenarios | The goal is a car or should override all other priorities |
| Missing information | Ask only when needed and label limitations | Missing equals zero |

Personalization should be explainable: "This estimate includes the school fees and parent support you entered" is useful. An unexplained score is not a substitute. Update user-controlled plans as information changes, but preserve a distinction between current estimates, prior scenarios and historical facts.

## 6. Flexible goals and sensitive decisions

A goal is broader than a purchasable item. Users may want to prepare for education, support family, change cities, cope with reduced income, build a reserve, or understand a tradeoff before choosing a target.

Suggested interaction:

1. Ask what the user wants to decide or achieve.
2. Identify which known information is relevant.
3. Ask for missing amounts, dates, constraints or preferences.
4. Explain the calculation and assumptions.
5. Offer comparisons the user controls: target, timing, contribution or other approved parameters.
6. Explain consequences for existing commitments and other goals.
7. Let the user save, revisit and revise the decision.

Not every question needs a chatbot. A guided workflow can ask dynamically. Provider choice and sending financial data to an LLM are separate decisions. The app should not shame users, promise outcomes or turn a preference into an investment suitability determination.

## 7. Existing manual records and transaction memory

The owner reconfirmed: **retain approved parsed records; delete original statements.**

The desired journey is record input → validate/parse → user review/correction → approved structured records → updated analysis. Users should not need to reopen original statements to see their recorded expenses. Record memory means authorized structured history, categories, provenance appropriate to the approved retention design and corrections—not a downloadable archive of originals.

Current supported CSV/Excel layouts do not prove support for notebooks, photos, arbitrary PDFs or every spreadsheet. Clarify which manual-record formats matter before selecting parsers/OCR. Do not send scans to an external OCR/LLM service without approval.

Keep user-entered planned expenses distinct from imported actuals. Avoid duplicate imports and misleading totals. Uncertain rows require review or explicit deferral. A new record must not silently overwrite a questionnaire answer or financial plan; show discrepancies and let the user decide which planning assumptions to update.

Approved structured history is still sensitive. Access controls and appropriate retention remain necessary even after original files are deleted.

## 8. Rainy-day fund: what should be kept?

The owner wants the app to help users understand this question, not to assume one answer for everyone. Existing approved behavior allows user-selected essential monthly expenses and coverage months:

`illustrative reserve target = selected essential monthly costs × chosen coverage months`

Show current earmarked reserve, remaining gap and effect of a user-chosen contribution. Clarify which funds are actually accessible; do not treat all investments as liquid savings. Any recommended range or individualized recommendation requires a separately approved, sourced methodology. No particular reserve size is being prescribed by this requirements document.

## 9. Bank research and education deliverable

The bank visit is project research, not a questionnaire item a customer must complete. The customer-facing questionnaire can capture existing products, learning interests and supplied terms. The research supplies verified educational material and product facts later.

Proposed bank-research checklist:

- Product name, institution, source/contact and verification date.
- Eligibility, minimum contribution/balance, tenure and rate validity.
- Interest/compounding conventions and payout timing.
- Fees, missed-payment rules, withdrawal restrictions and premature closure.
- Available account-opening/service channels and relevant infrastructure.
- Clearly identify whether a statement came from official documentation or an informal conversation.

Do not fabricate a visit, current rates, bank partnership or account integration. Rates and terms need verification when presented; this document has not researched current schemes. Ask what "infrastructure" specifically means before expanding that research scope.

## 10. Three proposed USPs and how to validate them

"Not in the market" remains a research question. These are candidate differentiators, not established exclusivity claims:

1. **An evolving financial profile connected to action:** setup and later edits meaningfully shape spending views, commitments, learning and flexible goal planning.
2. **Private, understandable decision exploration:** help beginners compare sensitive choices with explicit inputs and tradeoffs, rather than unexplained advice or generic calculators.
3. **Reviewed transaction memory with original-file deletion:** retain useful structured history and user-confirmed money-flow analysis without an archive of uploaded statements.

Research current competitors and target users before claiming uniqueness or paid value. Identify overlaps, alternatives, dated evidence and actual user benefit. These USPs are project positioning deliverables, not customer questions such as "what are our three USPs?" Optional feedback about user needs may help validate them, subject to approved design.

## 11. Acceptance criteria for a proposed implementation

- Every owner-listed financial topic has a setup location and a discoverable later-entry/edit route.
- Users can proceed with permitted incomplete sections; missing information remains explicitly unknown.
- Individual/family scope is clear and enforced; visibility of sensitive personal details is explicitly designed.
- Saved answers survive sign-out/restart and can be reviewed or corrected with proper authorization.
- Relevant screens use the same reviewed profile/planning values rather than disconnected duplicate copies.
- Groceries remain visible as a priority and their subitems are not counted twice.
- Periodic bills and investment/reserve allocations are labeled correctly.
- Manual/imported actuals do not silently replace planning values or duplicate obligations.
- Statement originals cannot be reopened; approved entries remain available under authorized records/categories.
- Goals accept user-defined purposes; examples do not become mandatory categories or the sole workflow.
- Outputs explain the inputs, assumptions and data gaps; unknown values do not produce confident recommendations.
- Android setup/editing and representative decision journeys are tested on the physical device.
- Documentation distinguishes delivered features from pending requirements and unvalidated market claims.

These criteria define intended behavior. They do not certify the current app or establish that the whole scope fits the November 11 deadline.

## 12. Decisions still needed before implementation

Ask in small groups relevant to the next approved task:

- Minimum required setup fields and exact skip/draft/save behavior.
- Personal versus household visibility, including privately explored goals.
- Required manual-record formats and their priority.
- How periodic obligations and goal funding interact with current monthly planning.
- Which personalization behavior is required for the immediate demo versus later delivery.
- Approved reserve guidance methodology, if recommendations beyond user-chosen scenarios are desired.
- Definition of bank infrastructure research and who will conduct the visit.
- Exact fields for schemes/insurance/holdings; avoid collecting unnecessary identifiers or medical details.

The clarification that goals are general removes the earlier suggestion to treat a car journey as an assumed first priority. Select the first representative journey with the owner.

## 13. Instructions for Claude and continuity

The owner explicitly welcomes suggestions that improve the user experience. Proactively present opportunities, explain the user problem, proposed improvement, benefits, tradeoffs and deadline impact, and ask for approval before implementing. Do not silently limit your review to the existing design or treat a promising idea as an approved requirement.

Treat this as the latest questionnaire/personalization clarification. Read the broader vision, living context and current code before editing. Inspect Git status and preserve concurrent work. Existing uncommitted goal-related files were observed during this documentation pass; their presence does not prove they are integrated or tested.

Propose a concrete implementation batch with fields, workflow, persistence, privacy boundaries and tests; obtain approval. Reuse current financial services and keep code concise. Do not rewrite the app merely to reproduce a prototype appearance. Do not claim all questionnaire requirements are implemented because the existing monthly-plan form contains some of them.

Maintain `docs/PROJECT_CONTEXT.md` and `CHANGELOG.md` after approved decisions and completed work. This document changes no application behavior, database schema or retention policy; it confirms requirements and records the owner's statement-memory clarification.
