# Artha AI Stitch-inspired prototype

This working copy applies the Stitch green/white fintech visual direction to the existing Flask/Jinja application.

## Implemented in this prototype
- Reworked account creation into a seven-step flow: account details, personal information, income, monthly expenses, loans/liabilities, savings/assets, goals/lifestyle.
- Captures the onboarding answers on the new user's `users.onboarding_answers` JSON field and marks onboarding complete.
- Creates a personal household workspace and a blank primary savings account after successful account creation, so CSV/Excel import is available immediately.
- Adds a Stitch-inspired dashboard with account-specific onboarding metrics and links to existing transactions, CSV/Excel import, analysis, goals, monthly plan, city comparison and assistant features.
- Adds a locality-tier comparison prototype (budget-friendly, mid-range, premium) with editable monthly costs for rent, groceries, milk/produce, food, transport, utilities, connectivity, healthcare/personal care and other spending.
- Keeps the existing audited city rent benchmark separate. The current city dataset's total-cost field is not used as a verified full cost-of-living value.
- Retains original Stitch HTML, design tokens and screenshots in `design/stitch_reference/`.

## Important limitations
- The uploaded Stitch exports provide a dashboard and an Income Details screen, not the complete Disha AIML questionnaire. The six-step form here is a working structure based on the Artha AI requirements document and the financial categories already present in the project. It is not represented as an exact copy of Disha's question wording or sequence.
- Onboarding answers are saved per user in JSON. The prototype dashboard uses these answers for its initial cards. A subsequent production pass should map the answers into the existing `ProfileItem` records so the profile editor, household visibility rules and planning modules share one canonical data model.
- The locality comparison is an editable scenario calculator. It does not persist values or claim that blank/default numbers are market benchmarks. Populate it with sourced locality data before presenting it as a factual market comparison.
- CSV/Excel import remains after account creation, because the existing importer requires an authenticated user, a household and an account. It is available immediately from the dashboard/workspace; users can skip it and import later.
- No original financial statements are added to this prototype. The existing review/approval import workflow is preserved.

## Apply locally
1. Back up your current working folder.
2. Replace its files with this prototype copy, or compare and cherry-pick the changed files.
3. Activate your project's virtual environment.
4. Run `alembic upgrade head` to apply migration `0014_onboarding_answers`.
5. Start the app with your existing local development command.
6. Test a fresh account, questionnaire submission, dashboard, imports, goals, plans and city comparison.
7. Run the full test suite before deploying. Do not push directly to the live Render service until these checks pass.
