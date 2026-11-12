# Artha AI — Agentic AI and Responsive UI Implementation

## Decisions

- Provider strategy: hybrid architecture supporting OpenAI and Google Gemini behind a provider-neutral interface.
- Autonomy: approval required before every state-changing action. No write-capable agent tools are enabled in the initial slice.
- Frontend: retain Flask/Jinja and the existing backend; progressively redesign the existing templates for desktop and mobile.

## Implemented in this build slice

### Responsive UI foundation

- Reworked the authenticated application shell with desktop sidebar navigation and mobile top/bottom navigation.
- Added shared Artha design tokens and responsive components to `app/static/app.css`.
- Redesigned the household landing/dashboard without inventing financial metrics that are not available in its route context.
- Added a first assistant workspace with starter prompts, household/month context selection and responsive composer.

### AI foundation

- Added a provider-neutral `ChatProvider` contract.
- Added OpenAI and Gemini REST adapters using Python's standard library.
- Added explicit provider selection; there is no silent cross-provider fallback because that would change where user prompts are sent.
- Added an authenticated, CSRF-protected `/api/v1/assistant/chat` endpoint.
- The assistant supports general financial education and optional read-only monthly analysis through the existing finance gateway. It receives only the selected household monthly summary, never raw transactions or bank statements.
- No conversation persistence or database migration has been introduced yet.

## Configuration

Set server-side environment variables:

```env
AI_DEFAULT_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
```

The browser sends the selected provider and conversation messages to the authenticated Flask API. API keys never reach the browser. Provider requests use a 35-second timeout. Provider failures are returned without logging prompt content.

## Explicit limitations

- Financial Analyst, Budget Planner, Goal Planner, Relocation Advisor and Investment Educator are not yet tool-connected autonomous agents.
- The assistant can inspect only the explicitly selected household monthly summary after the existing finance gateway validates membership. It cannot create plans, alter goals or execute financial actions.
- Chat history currently exists only in the current browser page; it is not persisted.
- The visual redesign currently covers the application shell, household landing page and assistant workspace. Other legacy pages inherit shared styling but still need page-by-page redesign.
- Mobile responsiveness is implemented in CSS but still needs real Android device testing.

## Next implementation steps

1. Expand read-only, household-scoped tools beyond the monthly summary (approved transaction categories, recurring commitments and goal summaries) using existing service functions and permission checks.
2. Add context assembly that minimises and redacts data before any model request.
3. Add structured action proposals and an approval record; revalidate actor, household access, state and CSRF at execution time.
4. Add durable conversation and approval models only after finalising retention and deletion rules.
5. Redesign each existing financial page and test at mobile breakpoints and on a physical Android device.
