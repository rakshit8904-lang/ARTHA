# Artha AI — Planning & Intelligence Batch (9 November 2026)

## Implemented in this batch

### Relocation estimate service
- Deterministic calculation accepts integer paise values for monthly income, rent, utilities, food, transport, other monthly costs, deposit months, moving costs and setup costs.
- Returns monthly cost, monthly surplus/deficit, rent burden, upfront cash requirement and explicit assumptions.
- Exposed as `POST /api/v1/households/<household_id>/relocation/estimate`.
- This is a scenario calculator, not a live rental quote or full city-specific relocation planner. Inputs are supplied by the user.

### Manual portfolio API and persistence
- Adds `portfolio_holdings` and Alembic revision `0009`.
- Supports manual asset types: mutual fund, equity, ETF, debt, gold, fixed deposit and other.
- Stores quantity, invested amount, manually entered current value, valuation date and notes.
- Exposes household-scoped list/create/delete endpoints.
- Owner-only writes; household membership required for reads. Current value is never fetched or implied to be live.
- Amounts are integer paise; quantity is decimal.

### Monthly summary API connection
- Registers the finance gateway to a read-only approved-ledger implementation at app startup.
- Exposes the existing monthly summary API through the connected gateway.
- Separates confirmed income and confirmed spending; reports unresolved debits/credits and excluded movements separately.
- Uses existing refund and spending aggregation semantics. No pending staged rows are included.
- Includes explicit notes that this is not a bank-verified balance or net-worth statement.

## Validation performed
- `compileall` passed for app, tests and migrations.
- Standalone relocation calculation smoke test passed.
- Full pytest/integration tests were not run: this execution environment does not have Flask installed. Run the full suite in the project's `.venv` after installing `requirements-app.txt`.
- Apply Alembic migration `0009` on a backed-up local test database before using portfolio endpoints.

## Not implemented yet
- No LLM-backed agents are included. The new deterministic services are the safe data layer for future relocation, investment and monthly-analysis agents.
- No portfolio HTML interface, live market-price integration, broker/bank connection, rental listing integration, or automatic investment transactions.
- Relocation estimates do not yet auto-populate city defaults or persist scenarios.

## API examples

Relocation request (all monetary fields in paise):

```json
{
  "monthly_income_minor": 5000000,
  "rent_minor": 1500000,
  "utilities_minor": 250000,
  "food_minor": 700000,
  "transport_minor": 300000,
  "other_minor": 400000,
  "deposit_months": 2,
  "moving_cost_minor": 500000,
  "setup_cost_minor": 300000
}
```

Create a portfolio holding:

```json
{
  "asset_name": "Example Nifty 50 Index Fund",
  "asset_type": "mutual_fund",
  "quantity": "125.50000000",
  "invested_minor": 2500000,
  "current_value_minor": 2675000,
  "as_of_date": "2026-11-09",
  "notes": "Manually entered valuation"
}
```
