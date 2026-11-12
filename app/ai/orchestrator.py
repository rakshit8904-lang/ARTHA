"""Permission-bounded multi-agent orchestration for Artha AI.

Agents are specialised prompt profiles selected locally. They have no direct database access.
Only the server may attach a minimised, household-authorised context object.
"""
import json

from app.ai.agents.registry import AGENTS, select_agent
from app.ai.tools.finance import build_financial_insights
from app.ai.router import get_provider


SYSTEM_PROMPT = """You are Artha AI, a careful personal-finance assistant for users in India.
Follow the specialist instructions supplied below. Use only user-provided information and
explicitly authorised context. Never invent balances, transactions, rates, tax rules, user
details or market data. Amounts in supplied backend summaries are integer paise unless
explicitly labelled otherwise. A blank, unknown or missing value is NOT zero. Preserve all
coverage warnings and never describe partial coverage as complete. Do not infer bank balance,
disposable income or net worth. Explain assumptions and uncertainty. Do not promise returns or
give personalised buy/sell instructions. You are currently READ-ONLY: never claim to have
changed a budget, goal, profile, transaction or portfolio. For any requested change, provide
a clearly labelled recommendation only and explain that approval-based execution is not yet
connected to this operation. Never ask the user to paste API keys, passwords or bank credentials.
Keep answers practical, clear and respectful."""


def route_agent(messages):
    latest = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
    return select_agent(latest)


def answer(messages, provider_name=None, financial_context=None, agent_name=None):
    agent_name = agent_name if agent_name in AGENTS else route_agent(messages)
    agent = AGENTS[agent_name]
    system_prompt = SYSTEM_PROMPT + "\n\nSPECIALIST ROLE: " + agent["label"] + "\n" + agent["instructions"]
    if financial_context is not None:
        monthly_summary = financial_context.get("monthly_summary", financial_context)
        context = {
            "monthly_summary": monthly_summary,
            "deterministic_insights": build_financial_insights(monthly_summary),
        }
        if financial_context.get("extended_household_context") is not None:
            context["extended_household_context"] = financial_context["extended_household_context"]
        system_prompt += "\n\nAUTHORISED FINANCIAL CONTEXT (read-only JSON):\n" + json.dumps(
            context, ensure_ascii=False, separators=(",", ":"))
    provider = get_provider(provider_name)
    reply = provider.complete(messages, system_prompt=system_prompt)
    if not isinstance(reply, str) or not reply.strip():
        from app.ai.providers.base import ProviderError
        raise ProviderError("The selected AI provider returned an empty response. Please try again.")
    return reply.strip(), agent_name
