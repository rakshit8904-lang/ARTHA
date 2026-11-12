(() => {
  const root = document.getElementById('assistant-app');
  if (!root) return;

  const form = document.getElementById('assistant-form');
  const input = document.getElementById('assistant-input');
  const messagesEl = document.getElementById('chat-messages');
  const welcome = document.getElementById('assistant-welcome');
  const send = document.getElementById('assistant-send');
  const providerStatus = document.getElementById('provider-status');
  const history = [];
  let busy = false;

  const money = value => '₹' + Math.round(value).toLocaleString('en-IN');

  function addMessage(role, content, pending = false, agentLabel = '') {
    welcome.hidden = true;
    const item = document.createElement('article');
    item.className = `chat-message ${role === 'user' ? 'user-message' : 'ai-message'}`;
    const label = document.createElement('span');
    label.className = 'message-label';
    label.textContent = role === 'user' ? 'YOU' : `ARTHA DEMO · ${(agentLabel || 'GUIDE').toUpperCase()}`;
    const body = document.createElement('p');
    body.textContent = content;
    if (pending) body.className = 'typing-indicator';
    item.append(label, body);
    messagesEl.appendChild(item);
    item.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    return { body, label };
  }

  function route(question) {
    const q = question.toLowerCase();
    if (/city|move|relocat|bengaluru|bangalore|delhi|mumbai|pune/.test(q)) return 'Relocation Advisor';
    if (/goal|save.*(₹|rs|rupee)|lakh|deadline|target/.test(q)) return 'Goal Planner';
    if (/invest|mutual fund|stock|rd|fd|risk|return/.test(q)) return 'Investment Educator';
    if (/budget|emi|loan|spend|expense|cash flow|income/.test(q)) return 'Budget Planner';
    return 'Financial Analyst';
  }

  function answer(question) {
    const q = question.toLowerCase();
    if (/where is my money|spend|expense|analyse|analyze/.test(q)) {
      return 'DEMO ANALYSIS\\n\\nYour sample monthly spending is grouped into housing, groceries, food, transport, utilities and personal costs. Start by reviewing the largest flexible category, then set a realistic monthly limit. Import a CSV statement in Spend to replace sample activity with your own transactions.\\n\\nDemo note: this response uses illustrative guidance, not live bank data.';
    }
    if (/budget|monthly plan|first.time earner|emi|loan/.test(q)) {
      return 'DEMO BUDGET PLAN\\n\\nA practical starting sequence is: (1) cover essential living costs, (2) reserve all required EMIs, (3) build a small emergency buffer, and (4) allocate what remains to your highest-priority goal. Avoid committing the same surplus to multiple goals.\\n\\nEnter your actual income, expenses and EMI in Financial Profile to calculate your own plan. This is a demonstration, not personalised financial advice.';
    }
    if (/goal|deadline|lakh|target/.test(q)) {
      return 'DEMO GOAL PLANNER\\n\\nFor a ₹1,00,000 goal over 12 months, the simple contribution is about ₹8,334 per month before interest or returns. If that amount does not fit your monthly surplus, extend the timeline or reduce the target. Keep emergency savings separate.\\n\\nThis example assumes zero investment return and is illustrative only.';
    }
    if (/city|move|relocat|bengaluru|bangalore|delhi|mumbai|pune/.test(q)) {
      return 'DEMO RELOCATION ADVISOR\\n\\nCompare the full monthly basket—not rent alone: housing, groceries, milk and produce, eating out, local transport, utilities, internet/mobile, healthcare and other everyday spending. Compare affordable, mid-range and premium localities using the same household size.\\n\\nAlso keep one-time moving costs (deposit, brokerage, travel and setup) separate from recurring monthly costs. The City Comparison tool lets you enter and compare these scenarios; its figures are user-entered estimates, not verified market prices.';
    }
    if (/invest|mutual fund|stock|rd|fd|risk|return/.test(q)) {
      return 'DEMO INVESTMENT EDUCATOR\\n\\nBefore choosing an investment, separate emergency money and near-term expenses from long-term money. Compare liquidity, risk, time horizon, fees and tax treatment. Fixed deposits and recurring deposits have different access and interest terms from market-linked funds, whose value can fall.\\n\\nThis demo provides education only; it does not recommend a specific product or promise returns.';
    }
    if (/emergency|financial security|buffer/.test(q)) {
      return 'DEMO FINANCIAL HEALTH CHECK\\n\\nBuild an emergency reserve gradually, based on essential monthly expenses and income stability. Keep it accessible and separate from goal or investment money. Review EMI-to-income, savings rate and essential-cost coverage together rather than relying on one score.\\n\\nUse your Financial Profile to enter actual values for a more meaningful calculation.';
    }
    return 'I’m Artha’s offline demonstration assistant. I can walk through budgeting, spending analysis, savings goals, loans/EMIs, relocation costs and investment basics. Try one of the suggested questions, or ask about one of those topics.\\n\\nDemo mode: responses are predefined educational examples. No Gemini API is connected, and no live financial data is being analysed.';
  }

  function submit(text) {
    const question = (text || '').trim();
    if (!question || busy) return;
    busy = true;
    input.value = '';
    input.style.height = 'auto';
    history.push({ role: 'user', content: question });
    addMessage('user', question);
    const pending = addMessage('assistant', 'Preparing demo response…', true);
    send.disabled = true;

    // Deliberately local: no API request, key, or external service is required.
    window.setTimeout(() => {
      const agent = route(question);
      const reply = answer(question);
      pending.body.textContent = reply;
      pending.body.classList.remove('typing-indicator');
      pending.label.textContent = `ARTHA DEMO · ${agent.toUpperCase()}`;
      history.push({ role: 'assistant', content: reply });
      providerStatus.textContent = 'Demo Mode · Offline responses · No API key required';
      providerStatus.classList.add('is-ready');
      providerStatus.classList.remove('is-missing');
      busy = false;
      send.disabled = false;
      input.focus();
    }, 350);
  }

  form.addEventListener('submit', event => {
    event.preventDefault();
    submit(input.value);
  });
  input.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = `${Math.min(input.scrollHeight, 150)}px`;
  });
  root.querySelectorAll('[data-prompt]').forEach(button => {
    button.addEventListener('click', () => submit(button.dataset.prompt));
  });
  document.getElementById('assistant-clear').addEventListener('click', () => {
    if (busy) return;
    history.length = 0;
    messagesEl.replaceChildren();
    welcome.hidden = false;
    input.value = '';
    providerStatus.textContent = 'Demo Mode · Offline responses · No API key required';
    input.focus();
  });

  providerStatus.textContent = 'Demo Mode · Offline responses · No API key required';
  providerStatus.classList.add('is-ready');
  providerStatus.classList.remove('is-missing');
})();
