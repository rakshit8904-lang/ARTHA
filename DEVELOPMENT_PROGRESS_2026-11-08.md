# Artha AI development progress — 8 November 2026

Baseline: `Artha_AI_Teammate_Package_2026-11-07.zip` (213 files). The corresponding workspace Git metadata identifies branch `solo/november-demo` at commit `8f92ba15b12ff885e29653b22b17a9930fc16c45`.

## Changes in this working copy

### 1. Test database isolation

- `tests/conftest.py` now always creates a per-test temporary SQLite database.
- `TEST_DATABASE_URL` is deliberately ignored by the shared fixture because the fixture drops and recreates all tables.
- `tests/test_test_database_safety.py` checks that an external database override cannot redirect the fixture.

### 2. Shared ledger aggregation

- `app/ledger/service.py` adds `spending_aggregation()` as the shared calculation path.
- `spend_totals()` remains backward-compatible for the Spend screen.
- `app/households/plans.py` now obtains monthly category actuals through the same service.
- The intended preserved rules are: purchases and fees count as confirmed spending; only matched purchase refunds reduce spending; a refund is attributed to its original purchase category in the month received; unmatched refunds are excluded; unclassified debit/credit values remain separate; transfers and other non-spending transaction types are excluded.
- `tests/test_ledger_aggregation.py` covers those cases and household membership enforcement.

### 3. Deterministic calculators

- `app/households/calculations.py` contains Decimal-based calculations with integer-paise outputs.
- Emergency reserve target months are user-selected; no universal month target is imposed.
- RD accepts monthly deposit, duration, annual rate, compounding convention and deposit timing. Quarterly compounding is converted to an equivalent monthly rate for the estimate; the UI states that actual bank rules may differ.
- `app/households/calculator_routes.py` adds a read-only household-scoped page at `/households/<household_id>/calculators`.
- `app/templates/calculators.html` and the household page link expose the calculators.
- `tests/test_household_calculations.py` covers arithmetic and route behavior.

### 4. City dataset audit (read-only)

- Added `reports/city_dataset_audit_2026-11-08.md`.
- The processed master has 221 unique city keys and no missing values in the ten numeric fields checked.
- Nellore and Surat have recorded rent greater than recorded total cost.
- The stored FX rate is 87.8638 INR/USD for every row, with no effective date. The processed master has no extraction date.
- Current LivingCost page labels its current headline as total with rent / without rent / rent and utilities, but the original source CSV is absent and current values differ from the packaged snapshot. The exact old-field mapping is therefore not approved.
- City affordability implementation remains paused to avoid double-counting or inventing a correction.


### 5. Savings goal planner (deterministic)

- Added a goal calculator for a user-defined target, current saved amount and monthly contribution.
- Reports remaining amount, funding percentage and estimated months to target.
- Assumes zero investment return; it does not recommend or project market-linked products.
- Uses Decimal-derived integer-paise inputs and outputs.

### 6. External rental-search helper

- Added a household-scoped form for city/locality, maximum rent, bedrooms and property type.
- Builds a URL-encoded Google search query focused on Magicbricks rental results.
- No scraping, listing ingestion, availability checks or price verification. The search terms are sent to the external search provider only when the user opens the link.
- Validates user-controlled filters and requires household membership.

## Verification performed

- Python `compileall`: passed for `app` and `tests`.
- AST parsing: passed for changed Python files.
- Jinja parsing: passed for all 20 templates.
- Manual pure-function smoke checks: passed for reserve arithmetic, zero-rate RD, monthly/quarterly compounding and beginning/end deposit timing.
- Migration files show a linear revision chain ending at `0007_housing`.

## Verification blocked

The full pytest suite could not start in this execution environment: `Flask` is not installed (`ModuleNotFoundError: No module named 'flask'`). Installing dependencies was also blocked by unavailable package-index network access. Therefore no application tests, route tests, SQLAlchemy integration tests, or browser checks are claimed as passing in this working copy. New savings-goal and rental-search tests have been added but are pending the combined test run.

No migration was added. No demo database was opened or modified. No source commit was created. The pre-existing dirty state in the workspace Git snapshot was left intact; only the files listed above were edited in this copy.

## Additional deterministic features — 8 November 2026

Implemented without agents, LLM calls, or external financial integrations:

1. **Monthly savings allocation** (`app/households/plans.py`, `app/templates/allocation.html`): allocates the saved monthly plan's calculated surplus across emergency reserve, other goals, and discretionary spending. It validates that allocations do not exceed surplus, is owner-write/viewer-read, and uses the monthly plan revision for stale-write protection. Values persist in the `monthly_plans.allocation` JSON column. It does not move money or create ledger transactions.
2. **Financial literacy centre** (`app/web/routes.py`, `app/templates/learning.html`): static educational explainers covering inflation, FD/RD, mutual funds/SIPs, risk/diversification, compounding, and emergency reserves. General education only.
3. **Recurring payment review** (`app/households/recurring.py`, `app/templates/recurring.html`, `app/models.py`): deterministic candidate heuristic based on approved debit purchases/fees with matching normalized description/category, at least three distinct calendar months, and amount variation within 15% of the median. User confirmation/dismissal is required; only confirmed labels persist. It does not claim subscriptions are certain and does not alter ledger records.

Migration `0008_planning_tools.py` adds the allocation JSON column and `recurring_expenses` table. Existing databases must run `python -m alembic upgrade head` before using these features. No migration was applied to a user/demo database in this environment.

Verification: Python compilation and Jinja parsing passed (23 templates). Full pytest/browser/database migration execution remains pending because Flask is not installed in this execution environment. Added `tests/test_planning_tools.py` for allocation persistence/bounds, recurring detection/confirmation, and household permissions; these tests have not been executed.
