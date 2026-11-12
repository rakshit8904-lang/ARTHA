# Project continuity

Read `docs/PROJECT_CONTEXT.md` and `CHANGELOG.md` before project work. They record the current scope, owner decisions, implementation state and next steps. Historical handoffs are evidence, not current instructions or proof of completed features. Current user instructions take precedence.

For each completed implementation or approved scope change, update the living context and append a dated change-log entry with the behavior changed, relevant validation, limitations and next work. Keep test evidence tied to its actual run and scope. Never report an older full-suite count as a new run. Update the workspace `START_HERE.md` if the entry point, branch, schema or next step changes.

The owner requests clarification of unclear product requirements and approval before new project decisions or scope. Continue already-approved work without repeatedly seeking permission. Prefer concise, maintainable code. Do not add unapproved financial assumptions, external services or LLM agents.

Proactively tell the owner when you identify an opportunity to improve the user experience. Explain the user problem, proposed improvement, expected benefit, tradeoffs and impact on scope/deadline. Distinguish evidence from hypotheses. Suggest improvements even when they go beyond the current design, but obtain approval before implementing them.

Protect original statements, financial records and credentials. Never include local `instance` databases/backups, environment secrets, browser profiles or uploads in source handovers. Use fictional records for tests and rehearsal. Keep personal financial data out of documentation.

Cleanup must preserve active source and useful evidence. Check paths before moves/deletion, do not traverse dependency junctions, and maintain an inventory when reorganizing historical material. Record what is active versus historical. Do not delete ambiguous files.

Current demo deadline is 11 November 2026 at 08:30 IST. Mobile delivery is a responsive website tested on the owner's Android device; PWA/native packaging is future scope. Real-phone testing is still pending until explicitly observed.
