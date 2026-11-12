// Confirmation before destructive actions, and select-all for review tables.
document.addEventListener("submit", function (event) {
  var message = event.target.getAttribute("data-confirm");
  if (message && !window.confirm(message)) {
    event.preventDefault();
  }
});
document.addEventListener("change", function (event) {
  if (event.target.id === "select-all") {
    document.querySelectorAll("input.row-check").forEach(function (box) {
      if (!box.disabled) { box.checked = event.target.checked; }
    });
  }
});
document.addEventListener("DOMContentLoaded", () => {
  const review = document.getElementById("review-deadline");
  if (!review) return;
  const clock = review.querySelector("time");
  let timer;
  function showDeadline(value) {
    clearTimeout(timer);
    const deadline = new Date(value);
    clock.dateTime = value;
    clock.textContent = deadline.toLocaleTimeString();
    timer = setTimeout(() => location.replace(review.dataset.return), Math.max(0, deadline - Date.now()));
  }
  showDeadline(clock.dateTime);
  if (!review.dataset.activity) return;
  let nextUpdate = 0;
  async function onActivity(event) {
    if (!event.isTrusted || Date.now() < nextUpdate) return;
    nextUpdate = Date.now() + 1000;
    try {
      const result = await fetch(review.dataset.activity, {
        method: "POST", headers: {"X-CSRF-Token": review.querySelector("[name=csrf_token]").value}
      });
      if (result.ok) showDeadline((await result.json()).expires_at);
      else if ([401, 403, 404, 409].includes(result.status)) location.replace(review.dataset.return);
    } catch { /* Keep the last server-confirmed deadline when offline. */ }
  }
  for (const action of ["input", "change", "keydown", "pointerdown", "wheel"]) {
    document.addEventListener(action, onActivity, {passive: true});
  }
});
document.querySelectorAll("form:has(.sheet-picker)").forEach(form => {
  const picker = form.querySelector(".sheet-picker");
  const sheet = picker.querySelector("select");
  const error = form.querySelector(".upload-error");
  const file = form.elements.file;
  file.addEventListener("change", () => {
    sheet.disabled = picker.hidden = true;
    sheet.value = "";
    error.hidden = true;
  });
  form.addEventListener("submit", async event => {
    if (!file.files[0]?.name.toLowerCase().endsWith(".xlsx")) return;
    event.preventDefault();
    const selectedFile = file.files[0];
    const button = form.querySelector("button");
    button.disabled = true;
    try {
      const response = await fetch(form.action, {
        method: "POST", headers: {Accept: "application/json"}, body: new FormData(form)
      });
      if (selectedFile !== file.files[0]) return;
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Upload failed.");
      if (result.review) { location.assign(result.review); return; }
      sheet.replaceChildren(new Option("Choose a worksheet", ""), ...result.sheets.map(name => new Option(name, name)));
      sheet.disabled = picker.hidden = false;
      error.hidden = true;
      sheet.focus();
    } catch (failure) {
      error.textContent = failure instanceof SyntaxError ? "Upload failed. Check your session and file size." : failure.message;
      error.hidden = false;
    } finally { button.disabled = false; }
  });
});
const monthlyPlan = document.getElementById("monthly-plan");
if (monthlyPlan) {
  const housing = monthlyPlan.elements.housing;
  const included = monthlyPlan.elements.maintenance_included;
  function showHousingFields() {
    for (const group of monthlyPlan.querySelectorAll("[data-housing]")) {
      const visible = group.dataset.housing === "maintenance"
        ? housing.value === "owned" || (housing.value === "rented" && included.value === "no")
        : group.dataset.housing === housing.value;
      group.hidden = !visible;
      group.querySelectorAll("input, select").forEach(field => { field.disabled = !visible; });
    }
    included.required = monthlyPlan.elements.Rent.required = housing.value === "rented";
  }
  housing.addEventListener("change", showHousingFields);
  included.addEventListener("change", showHousingFields);
  showHousingFields();
  const steps = Array.from(monthlyPlan.querySelectorAll("section"));
  const back = document.getElementById("plan-back"), next = document.getElementById("plan-next");
  let step = 0;
  function showStep(index) {
    step = index;
    steps.forEach((section, i) => { section.hidden = i !== step; });
    back.hidden = step === 0;
    next.hidden = step === steps.length - 1;
    document.getElementById("plan-save").hidden = !next.hidden;
  }
  function advance() {
    const invalid = steps[step].querySelector(":invalid");
    if (invalid) invalid.reportValidity();
    else showStep(step + 1);
  }
  next.addEventListener("click", advance);
  back.addEventListener("click", () => showStep(step - 1));
  monthlyPlan.addEventListener("keydown", event => {
    if (event.key === "Enter" && step < steps.length - 1 && event.target.tagName === "INPUT") {
      event.preventDefault(); advance();
    }
  });
  showStep(0);
}
