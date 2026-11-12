(() => {
  const form = document.getElementById('signup-onboarding');
  if (!form) return;

  const steps = [...form.querySelectorAll('.onboarding-step')];
  const pills = [...form.querySelectorAll('.step-pills span')];
  const back = document.getElementById('step-back');
  const next = document.getElementById('step-next');
  const submit = document.getElementById('step-submit');
  const fill = document.getElementById('progress-fill');
  const count = document.getElementById('step-count');
  const label = document.getElementById('step-label');

  const titles = [
    'ACCOUNT DETAILS',
    'PERSONAL INFORMATION',
    'INCOME DETAILS',
    'MONTHLY EXPENSES',
    'LOANS & LIABILITIES',
    'SAVINGS & ASSETS',
    'GOALS & LIFESTYLE'
  ];

  let current = 0;

  function toggleLoans() {
    const answer = form.querySelector('input[name="loan_has"]:checked');
    const loanFields = document.getElementById('loan-fields');
    if (loanFields) loanFields.hidden = answer?.value === 'no';
  }

  function show(index) {
    current = index;

    steps.forEach((step, i) =>
      step.classList.toggle('active', i === index)
    );

    pills.forEach((pill, i) => {
      pill.classList.toggle('current', i === index);
      pill.classList.toggle('done', i < index);
    });

    back.disabled = index === 0;
    next.hidden = index === steps.length - 1;
    submit.hidden = index !== steps.length - 1;

    fill.style.width = `${((index + 1) / steps.length) * 100}%`;
    count.textContent = `Step ${index + 1} of ${steps.length}`;
    label.textContent = titles[index];

    if (index === 4) toggleLoans();
  }

  function validCurrent() {
    const required = [...steps[current].querySelectorAll('[required]')];

    for (const field of required) {
      if (!field.checkValidity()) {
        field.reportValidity();
        field.focus();
        return false;
      }
    }

    return true;
  }

  form.querySelectorAll('input[name="loan_has"]').forEach(el =>
    el.addEventListener('change', toggleLoans)
  );

  back.addEventListener('click', () =>
    show(Math.max(0, current - 1))
  );

  next.addEventListener('click', () => {
    if (validCurrent()) {
      show(Math.min(steps.length - 1, current + 1));
    }
  });

  form.addEventListener('submit', e => {
    if (!validCurrent()) e.preventDefault();
  });

  show(0);
})();
