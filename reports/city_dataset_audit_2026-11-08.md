# City dataset audit — 8 November 2026

## Scope inspected

- `data/processed/city_master.csv`
- `reports/city_processing_log.md`
- `reports/data_inventory.md`
- `src/city_processing.py`
- Source URLs embedded in `city_master.csv`

The clean application package contains the processed city master but not the original raw LivingCost CSV or the original 30-city enrichment source file. The extraction/snapshot date is not recorded in the processed master.

## Structural checks

- 221 rows and 221 unique `city_key` values.
- No missing values in the ten numeric LivingCost/FX fields checked.
- All 221 `income_after_rent_usd` values equal `monthly_salary_after_tax_usd - rent_one_person_usd` within $0.11.
- All 221 INR `cost_one_person_inr` values match `cost_one_person_usd * usd_to_inr_rate_used` within ₹0.02.
- The stored FX rate is one value across the dataset: 87.8638 INR/USD. Its effective date is not present.
- 219 of 221 rows have `cost_one_person_usd >= rent_one_person_usd`.
- Nellore has cost $251 and rent $302; Surat has cost $322 and rent $458. These two records fail the expected rent-not-greater-than-total sanity check if `cost_one_person_usd` is interpreted as a total including rent.
- `months_covered` is not reliably reproduced by the simple ratio `monthly_salary_after_tax_usd / cost_one_person_usd` within 0.11 for all records (145/221 match). Its exact source definition or rounding/derivation is not recorded here.

## Source semantics and freshness

The current LivingCost Adoni page (https://livingcost.org/cost/india/ap/adoni) labels its headline fields as “Total with rent”, “Without rent”, and “Rent & Utilities”, and shows an update date of 21 June 2026 when inspected on 8 November 2026. The current site-wide About page (https://livingcost.org/about) describes its prices as crowdsourced and combined with other public datasets and warns that city prices vary and are intended for comparison rather than as a precise personal budget.

This current page structure is useful evidence about today's LivingCost presentation, but it does not prove the exact mapping of every column in the older processed CSV. The processed data contains no extraction timestamp, observation date, source snapshot, or per-row provenance beyond the city source URL. The CSV values for Adoni also differ from the current page values, so the current page must not be used to silently overwrite the older snapshot.

## Current conclusion

Do not implement or publish a city affordability total from this dataset yet. In particular:

1. Do not add the `rent_one_person` field to `cost_one_person` unless the original CSV's exact definitions establish that this is correct.
2. Do not subtract rent from the cost field or replace it with a current website figure without confirming the original field mapping and snapshot date.
3. Flag Nellore and Surat as anomalous under the “total includes rent” interpretation; do not silently repair them.
4. Keep the fixed FX rate and unknown extraction date visible as provenance limitations.
5. Family scaling, deposits, moving costs, utilities coverage and household assumptions remain unverified.

A city explorer may proceed only after the original source CSV or a reliable archived schema/data dictionary is recovered and the rent field mapping, extraction date and anomaly policy are approved. Until then, this is a read-only audit, not an approved calculation contract.

## External source references

- LivingCost Adoni: https://livingcost.org/cost/india/ap/adoni
- LivingCost About / data limitations: https://livingcost.org/about
