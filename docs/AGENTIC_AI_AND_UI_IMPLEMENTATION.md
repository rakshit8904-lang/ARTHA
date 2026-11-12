# Artha AI — Agentic AI and responsive UI implementation

## Decisions
- Hybrid provider support: OpenAI and Google Gemini adapters.
- Provider selection is explicit; there is no silent cross-provider fallback.
- Approval-first autonomy: no state-changing tools are exposed in this release.
- Existing Flask/Jinja/SQLAlchemy application and financial services are retained.
- One responsive web application serves desktop, tablet and mobile browsers.

## Implemented in this build
- Responsive application shell, mobile top bar and bottom navigation.
- Redesigned dashboard and assistant workspace, retaining existing route contracts.
- Specialist routing for Financial Analyst, Budget Planner, Goal Planner, Relocation Advisor,
  Investment Educator and Financial Companion.
- Deterministic local routing; it does not spend an extra model call.
- Provider-neutral chat adapter for OpenAI and Gemini.
- Authenticated assistant status endpoint that reports key presence only (never the key).
- Authenticated, CSRF-protected chat endpoint.
- Optional household/month context using the existing authorised monthly-summary gateway.
- Deterministic paise-to-rupee metrics; missing values remain missing.
- Conversation state remains in the browser tab; it is not persisted to the database.
- AI keys are loaded from server environment variables / local `.env`.

## Explicit current limitations
- Agents are specialised model instructions, not unrestricted autonomous processes.
- The only financial context connected to chat is the selected, minimised monthly summary.
  Profile, saved goals, portfolio and budget-plan data are not yet exposed as agent tools.
- Agents cannot write to budgets, goals, profile, transactions or portfolio. No approval queue
  or execution endpoint is enabled. The UI and API state this explicitly.
- No live bank, broker, market, email or SMS integrations.
- No streaming responses or durable conversation history.
- No native Android/iOS application; mobile support is responsive browser UI.
- Real-device testing and full regression tests remain required.

## API key setup
1. Copy `.env.example` to `.env` in the repository root (same directory as `wsgi.py`).
2. Add one or both keys:
   - `OPENAI_API_KEY=...`
   - `GEMINI_API_KEY=...`
3. Set `AI_DEFAULT_PROVIDER=openai` or `AI_DEFAULT_PROVIDER=gemini`.
4. Keep `.env` out of Git. Never place keys in HTML, JavaScript, screenshots or chat messages.
5. Restart the Flask/Gunicorn process after changing `.env`.
6. In Artha Assistant, choose the provider whose key is configured.

For local development, `python-dotenv` loads `.env`. Production deployments should configure
these values as host-level environment secrets instead of uploading `.env`.

## Next engineering gates
1. Add a persistent conversation model with retention and delete controls.
2. Add explicit read-only tools for plans, goals, profile and manual portfolio values, respecting
   household membership and private-goal/profile visibility.
3. Add a pending-action model and auditable approval lifecycle.
4. Implement individual deterministic executors (starting with a monthly-plan change), each
   revalidating owner permissions and revision numbers at approval time.
5. Add per-user AI rate limiting, provider cost controls and structured redacted telemetry.
6. Add end-to-end mobile tests and verify Android/iOS browsers.
