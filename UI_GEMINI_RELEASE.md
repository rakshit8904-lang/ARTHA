# Artha AI — unified UI and Gemini release

This build updates the shared desktop/mobile shell, normalizes legacy financial forms and tables, and removes provider selection from the assistant. The assistant API **enforces Gemini on the server**, even if a client supplies `provider=openai`. The Gemini API key remains server-side.

## Configure

Copy `.env.example` to `.env` and set `GEMINI_API_KEY=your_key_here`. Do not commit `.env`. Restart the Flask process after changing the key.

## Scope and limits

Existing pages, workflows and Flask/Jinja routes are retained. Agent capabilities are still read-only; no approval/execution engine or persistent chat history has been added. Responsive CSS is included for all legacy pages, but physical-device visual QA remains required. The reference site was not visually accessible, so this is a cohesive UI implementation rather than a pixel-perfect copy.
