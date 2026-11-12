# Manual portfolio interface

Implemented 9 November 2026. Open a household and choose **Portfolio**.

Owners can add and edit a holding's name, asset type, quantity, invested amount, manually entered current value, valuation date and notes. Saved holdings reopen with their values. Viewers can inspect holdings and totals but cannot save changes. Household access checks and CSRF protection apply. Stale edit timestamps are rejected to prevent another tab's changes being overwritten.

The page displays aggregate invested/current values, their difference and a simple percentage relative to invested amount. Zero invested value produces an undefined percentage, not a division error. Valuation dates are visible on every holding; a mixed-date total is labelled accordingly. This is not an annualized return or total performance measure and does not incorporate dividends, withdrawals, taxes or fees unless the entered values reflect them.

All prices are manual. No broker, bank, NAV feed, trade execution or investment recommendation was added. Portfolio edits do not change monthly budgets or transaction records. The existing JSON create endpoint and new HTML forms use the same validation function. Existing list/delete APIs remain available; no new deletion control or JSON edit endpoint was added in this interface task.

Routes are `/households/<household_id>/portfolio` and `/households/<household_id>/portfolio/<holding_id>`. The existing portfolio table is reused, so no schema migration is required and the database remains at **0010**.

Regression tests cover create/edit/reopen, stale updates, household and viewer permissions, CSRF rejection, invalid amounts/quantities/dates, zero invested amount and HTML escaping. Nine targeted portfolio and handoff integration tests passed. Headless Edge checks passed at **360px, 390px and 1280px**, with CSRF enabled and no page overflow or JavaScript errors. Evidence is in `outputs/QA/portfolio_20261109`. A physical-phone rehearsal is still pending.

Full suite: **166 passed, 1 PostgreSQL-only skip, 7 warnings**, in 94.78 seconds.

The next planned demo work is fuller monthly-summary presentation, followed by real-device rehearsal and the final document/package. Historical handoff descriptions that call the portfolio API-only predate this interface.

Evidence paths beginning with `outputs/` are relative to the workspace root. For current status after this milestone, see [project context](PROJECT_CONTEXT.md).
