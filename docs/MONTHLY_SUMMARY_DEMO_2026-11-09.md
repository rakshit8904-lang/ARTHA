# Expanded monthly summary

Implemented 9 November 2026. Open a household and choose **Monthly summary**. The page defaults to the current month in India time and supports switching months.

The summary presents confirmed income, net spending and their difference, followed by category totals, unclassified debits/credits and excluded movements. Review links preserve the selected month and take users to the ledger, monthly budget, unclassified entries or refunds.

Category amounts use the existing purchase/fee/matched-refund calculation. Refunds are attributed to the original purchase category in the month received. Negative category amounts are explicitly explained. Unmatched refunds are now exposed as a separate excluded amount without changing the spending calculation.

Transfers remain gross ledger-leg volumes, potentially including both sides. Investment movements include both incoming and outgoing amounts. Neither is represented as extra spending. Loan payments and other excluded movements are not deducted from the displayed income-minus-spending difference. The page explains that this is not a bank balance or disposable income.

Empty months show unknown totals rather than invented zero income/spending. Recorded months retain partial coverage because complete account coverage has not been confirmed. Even zero unclassified entries cannot establish completeness. Household permissions remain enforced, and the screen is read-only.

Validation: **22 targeted tests passed**, covering finance semantics, shared aggregation, integration and the expanded presentation. Cases include a prior-month purchase refunded in the selected month, unmatched refunds, two transfer legs, loan payments, unclassified movements, pending-row exclusion, viewer/nonmember access, review links and empty/invalid months. No full-suite rerun was needed for this presentation increment; the prior portfolio checkpoint had 166 passing tests and one PostgreSQL-only skip.

Headless Edge checks at **360px, 390px and 1280px** passed expected totals, month switching and empty states with no page overflow or JavaScript errors. Evidence is in `outputs/QA/summary_20261109`. Physical-phone/network rehearsal remains outstanding.

No schema migration, financial policy, LLM agent, investment recommendation or transaction write was added. Database revision remains **0010**. The next release-readiness step is an actual-device end-to-end rehearsal, followed by the updated final document and source package for 11 November at 08:30 IST.

Evidence paths beginning with `outputs/` are relative to the workspace root. For current status after this milestone, see [project context](PROJECT_CONTEXT.md).
