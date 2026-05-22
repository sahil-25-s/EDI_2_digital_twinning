/** Shared UI utilities */
function initPasswordToggles() {
  document.querySelectorAll("[data-toggle-password]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-toggle-password");
      const input = document.getElementById(id);
      if (!input) return;
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.textContent = show ? "Hide" : "Show";
    });
  });
}

function bindSlider(sliderId, outputId, inputId, formatter = (v) => v) {
  const slider = document.getElementById(sliderId);
  const output = document.getElementById(outputId);
  const input = document.getElementById(inputId);
  if (!slider || !output) return;

  const sync = (val) => {
    const v = formatter(val);
    output.textContent = v;
    if (input) input.value = val;
  };
  slider.addEventListener("input", () => sync(slider.value));
  if (input) {
    input.addEventListener("change", () => {
      slider.value = input.value;
      sync(input.value);
    });
  }
  sync(slider.value);
}

function initSliders() {
  document.querySelectorAll("[data-slider]").forEach((slider) => {
    const target = slider.getAttribute("data-slider");
    const output = document.querySelector(`[data-slider-out="${target}"]`);
    const input = document.querySelector(`[data-slider-input="${target}"]`);
    const fmt = slider.getAttribute("data-format");
    const formatter =
      fmt === "dec1" ? (v) => Number(v).toFixed(1) : fmt === "int" ? (v) => String(Math.round(v)) : (v) => v;

    const sync = (val) => {
      const display = formatter(val);
      if (output) output.textContent = display;
      if (input) input.value = val;
    };
    slider.addEventListener("input", () => sync(slider.value));
    if (input) {
      input.addEventListener("change", () => {
        slider.value = input.value;
        sync(input.value);
      });
    }
    sync(slider.value);
  });
}

function setFormFields(form, data) {
  if (!data) return;
  Object.entries(data).forEach(([name, value]) => {
    let el = form.elements[name];
    if (!el) return;
    if (el instanceof RadioNodeList || (el.length && el[0]?.type === "checkbox")) {
      const checkbox = [...el].find((n) => n.type === "checkbox");
      if (checkbox) checkbox.checked = Number(value) === 1;
      return;
    }
    if (el.type === "checkbox") {
      el.checked = Number(value) === 1;
      return;
    }
    if (name === "alcohol_consumption" && String(value).toLowerCase() === "none") {
      el.value = "";
      return;
    }
    el.value = value ?? "";
  });
  initSliders();
}

function riskBadge(score, invert = false) {
  const v = Number(score);
  const effective = invert ? 100 - v : v;
  if (effective >= 65) return '<span class="badge badge-high">High</span>';
  if (effective >= 40) return '<span class="badge badge-mid">Moderate</span>';
  return '<span class="badge badge-low">Low</span>';
}

function renderRing(label, value, color, invert = false) {
  const v = Math.round(Number(value));
  const p = invert ? v : v;
  return `<div class="ring-wrap"><div class="ring" style="--p:${p};--c:${color}"><div class="ring-inner">${v}</div></div><span class="text-muted">${label}</span></div>`;
}

function drawTrendChart(canvasId, history) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !window.Chart || !history?.length) return;
  const labels = history.map((h) => `Day ${h.day}`);
  const energy = history.map((h) => h.state?.energy_level ?? 0);
  const fatigue = history.map((h) => h.state?.fatigue_level ?? 0);
  new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [
        { label: "Energy", data: energy, borderColor: "#2563eb", tension: 0.35, fill: false },
        { label: "Fatigue", data: fatigue, borderColor: "#d97706", tension: 0.35, fill: false },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom" } },
      scales: { y: { min: 0, max: 100 } },
    },
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initPasswordToggles();
  initSliders();
});
