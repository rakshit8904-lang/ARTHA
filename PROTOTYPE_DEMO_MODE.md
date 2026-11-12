# Artha AI demo mode

- The assistant UI now uses deterministic, local educational demo responses. It does not call Gemini or any external AI API.
- Responses are explicitly labelled as demo examples and must not be presented as live AI analysis.
- The city/locality comparison totals only user-entered amounts. They are not verified market prices.
- The city comparison JavaScript is served as a static file so it works under the existing `script-src 'self'` CSP.
- The registration questionnaire remains seven sections in the current project. Exact Disha prototype wording still requires the source questionnaire.
- Existing Flask authentication, database, transaction, import, goal and plan routes have not intentionally been replaced.
