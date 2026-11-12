# City Affordability Engine — implementation note

## Delivered in this build

- Added a read-only city comparison service backed by `data/processed/city_master.csv`.
- Added an authenticated household page at `/households/<household_id>/city-affordability`.
- Added city-name filtering across the 221 packaged city records.
- Calculates the dataset's one-person rent benchmark as a share of user-entered monthly take-home income, and shows income remaining after that rent benchmark.
- Shows per-row source links and labels the four rent-burden bands as illustrative.
- Does not write to the ledger, change a monthly plan, or persist the income entered into the comparison.

## Data contract and safety boundary

The source audit found 221 unique city keys and no missing values in the checked numerical LivingCost/FX fields. However, the processed file has no extraction timestamp, the fixed FX rate (87.8638 INR/USD) has no effective date, and the exact semantics of the source-reported total-cost field are not established. Nellore and Surat are anomalies under the interpretation that total cost includes rent.

Accordingly, this version uses only `rent_one_person_inr` for the rent-burden calculation. It retains the source-reported cost as unused context in the service row but does not add it to rent, subtract rent from it, or claim it is a verified all-in monthly budget. No family scaling, locality-level pricing, maintenance, deposit, moving-cost or utility assumptions are made. After-rent income is not disposable income.

## Verification

- `compileall` passed for the application and new test module.
- Standalone service checks passed: 221 unique records loaded, Cuttack search returned a match, all 221 records were compared and sorted by rent share, and Nellore/Surat source values were retained without automatic repair.
- The pytest suite could not start in this build container because Flask is not installed (`ModuleNotFoundError: flask`). The new pytest module is included but requires the project's dependency environment. No full application/browser regression is claimed.

## Next work

Recover the original source schema/snapshot or an authoritative data dictionary before adding an all-in cost-of-living total. Then add explicit user-entered household size, rent override, utilities and recurring expense inputs before a relocation scenario. Keep upfront deposit/moving costs separate from monthly affordability.
