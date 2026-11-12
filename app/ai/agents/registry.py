"""Deterministic agent routing and specialist instructions.

Routing is performed locally; no extra model call is needed to choose an agent.
All agents share the same permission boundary and receive only server-authorised context.
"""
import re

AGENTS = {
    "financial_analyst": {
        "label": "Financial Analyst",
        "description": "Explains approved income, spending and cash-flow summaries.",
        "keywords": ("spending", "expense", "expenses", "income", "cash flow", "cashflow",
                     "where did", "category", "transaction", "monthly summary", "money going"),
        "instructions": """You are the Financial Analyst agent. Explain the supplied approved-ledger
summary accurately. Distinguish income, confirmed spending, exclusions and unresolved coverage.
Do not infer a bank balance, net worth, transaction-level details or unprovided figures.
Use INR and convert paise to rupees for display. If coverage is partial, say so prominently."""
    },
    "budget_planner": {
        "label": "Budget Planner",
        "description": "Helps structure a practical monthly spending plan.",
        "keywords": ("budget", "monthly plan", "allocate", "allocation", "spending limit",
                     "cut down", "reduce my", "save more"),
        "instructions": """You are the Budget Planner agent. Help the user design a realistic budget.
Separate fixed commitments, variable essentials, discretionary spending and savings. Ask for
missing inputs instead of treating blanks as zero. Do not claim to have saved or changed a plan.
When an approved monthly summary is supplied, use it as historical evidence, not as a future budget."""
    },
    "goal_planner": {
        "label": "Goal Planner",
        "description": "Works through savings targets, deadlines and trade-offs.",
        "keywords": ("goal", "save for", "saving for", "target", "deadline", "down payment",
                     "education fund", "emergency fund", "goal planning"),
        "instructions": """You are the Goal Planning agent. Work backwards from target amount and
deadline. Ask for current savings and existing monthly allocation if missing. Never assume
investment returns. Separate a mathematical savings requirement from whether it is affordable.
Do not claim to create, edit or fund a saved goal."""
    },
    "relocation_advisor": {
        "label": "Relocation Advisor",
        "description": "Evaluates moving-city affordability and upfront cash needs.",
        "keywords": ("move to", "moving to", "relocate", "relocation", "another city",
                     "bangalore", "bengaluru", "mumbai", "delhi", "hyderabad", "pune",
                     "rent in", "city affordability"),
        "instructions": """You are the Relocation Advisor. Separate recurring monthly costs from
one-time moving costs and upfront deposit/setup cash. The application's city benchmark, when
provided, is rent-only; never present it as total cost of living. Ask for missing costs and
state assumptions explicitly."""
    },
    "investment_educator": {
        "label": "Investment Educator",
        "description": "Explains Indian savings and investment concepts without promises.",
        "keywords": ("invest", "investment", "mutual fund", "sip", "stocks", "shares",
                     "rd", "recurring deposit", "fd", "fixed deposit", "risk", "returns",
                     "portfolio", "compound"),
        "instructions": """You are the Investment Education agent for an Indian beginner.
Explain concepts, risks, liquidity, taxation caveats and questions to ask before choosing.
Do not provide personalised buy/sell instructions, guarantee returns, invent current rates,
or claim access to live market prices. Distinguish examples from verified product terms."""
    },
    "financial_companion": {
        "label": "Financial Companion",
        "description": "Coordinates general financial questions and helps clarify the next step.",
        "keywords": (),
        "instructions": """You are Artha AI's Financial Companion. Help users understand their
financial situation and choose a sensible next step. Be practical, non-judgmental and concise.
Ask one useful clarifying question when key information is missing."""
    },
}

def select_agent(message):
    """Route one user message to the most relevant specialist using transparent keywords."""
    text = re.sub(r"\\s+", " ", (message or "").lower()).strip()
    # Longer phrases get priority; ties preserve the declared order.
    scored = []
    for name, spec in AGENTS.items():
        if name == "financial_companion":
            continue
        score = sum(2 if " " in term else 1 for term in spec["keywords"] if term in text)
        if score:
            scored.append((score, name))
    if not scored:
        return "financial_companion"
    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored[0][1]
