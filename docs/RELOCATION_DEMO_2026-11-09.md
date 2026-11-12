# Saved relocation scenarios

Implemented 9 November 2026 after owner approval. Demo deadline remains 11 November at 08:30 IST, with a responsive website for laptop and phone browsers.

## Try the feature

Open a household and choose **Plan a move**. Choose a destination and press **Use city and reset inputs**. This loads that city's editable one-person rent benchmark. Enter income, utilities/maintenance, food, transport, other monthly commitments, deposit months, moving costs and setup costs. Enter an explicit zero when a cost does not apply.

**Calculate** previews the estimate without changing saved data. **Save scenario** saves a named scenario for the household. Reopen it from the saved list, edit and save again. A stale edit is rejected rather than overwriting changes from another tab.

**Reset inputs** restores the selected city's dataset rent and clears the other financial inputs. A saved scenario remains unchanged until Save scenario is used. The saved scenario's name is retained while editing. Monthly budgets and transaction history are never modified by this feature.

Owners can save and edit. Viewers can read and calculate, but cannot persist changes. Other households cannot access the scenario, even by changing IDs in URLs.

## What results mean

- Monthly costs are rent plus utilities/maintenance, food, transport and other monthly costs.
- Monthly surplus/shortfall is entered income minus those costs. Break-even explicitly means no remaining buffer.
- Upfront cash is rent multiplied by deposit months, plus moving and setup costs. It excludes first-month living costs and an emergency reserve, which are explained on the screen.
- Zero income has no defined rent-burden percentage. No division error or invented percentage is shown.
- Only rent is prefilled. City data has unknown snapshot/FX dates and supplies no verified family/locality quote or reliable total living-cost estimate. The user can override rent.
- The result is a scenario estimate, not a guarantee of affordability or proof of available funds. There is no LLM agent or listing feed.

## Implementation and verification

Routes: `/households/<household_id>/relocation` and `/households/<household_id>/relocation/<scenario_id>`.

The existing deterministic relocation function remains the single calculation path. Inputs are converted from rupees to integer paise on the server. `RelocationScenario` stores household ID, name, city key, input JSON, revision and update time. Migration **0010** creates its own table; it does not modify transaction or budget records.

Full regression: **163 passed, 1 PostgreSQL-only skip, 7 warnings**, in 141.59 seconds. Five new tests cover save/reopen/edit/stale revisions, reset and calculation isolation, household/owner/viewer/CSRF protection, invalid inputs, and zero-income/break-even results. Schema/model comparison also passed.

Headless Edge checks at **360px, 390px and 1280px** passed save, reopen, edit and reset flows with CSRF enabled, no page overflow and no JavaScript errors. Screenshots and results are under `outputs/QA/relocation_20261109`. This does not replace a physical-phone rehearsal.

A disposable copy of the existing database passed 0009 -> 0010 -> 0009 -> 0010 with original rows preserved. The active database was backed up under ignored `instance/before-relocation-0010-2026-11-09.sqlite3` and upgraded to 0010; original rows, integrity and foreign keys were checked.

Remaining work outside this feature: manual portfolio UI/editing, fuller monthly-analysis presentation, real-device connectivity/rehearsal and the final document/package. The earlier 70% assessment was the pre-relocation baseline, not a new claim that all remaining work is done.

Evidence paths beginning with `outputs/` are relative to the workspace root. For current status after this milestone, see [project context](PROJECT_CONTEXT.md).
