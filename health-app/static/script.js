// ---------------------------------------------------------------------
// FuelUp front-end logic
// ---------------------------------------------------------------------

const state = {
  foods: null,          // full food DB, fetched once from /api/foods
  profile: null,        // last calculated profile (targets, macros, etc.)
  plate: [],            // items the student has added: {id, group, label, unit, qty, kcal, protein, carbs, fat}
};

const GROUP_COLORS = {
  protein: "#5B5FD6",
  fiber: "#3F8F5C",
  carbs: "#E8A33D",
};

let macroChart = null;

// ---------------- init ----------------
document.addEventListener("DOMContentLoaded", async () => {
  state.foods = await fetch("/api/foods").then(r => r.json());
  wireForm();
  wirePlateBuilder();
});

// ---------------- profile form ----------------
function wireForm() {
  const form = document.getElementById("profile-form");
  const errorEl = document.getElementById("form-error");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.textContent = "";

    const payload = {
      name: document.getElementById("name").value,
      age: document.getElementById("age").value,
      sex: document.getElementById("sex").value,
      height: document.getElementById("height").value,
      weight: document.getElementById("weight").value,
      activity: document.getElementById("activity").value,
      goal: document.getElementById("goal").value,
      diet_type: document.getElementById("diet_type").value,
    };

    let res, data;
    try {
      res = await fetch("/api/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      data = await res.json();
    } catch (err) {
      errorEl.textContent = "Something went wrong reaching the server. Please try again.";
      return;
    }

    if (!res.ok) {
      errorEl.textContent = data.error || "Please check your inputs.";
      return;
    }

    state.profile = data;
    state.plate = []; // reset plate on a fresh calculation
    renderDashboard(data);
    setupFoodGroups(data.diet_type);
    renderPlate();

    document.getElementById("dashboard").classList.remove("hidden");
    document.getElementById("plate-builder").classList.remove("hidden");
    document.getElementById("dashboard").scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

function renderDashboard(data) {
  document.getElementById("dash-heading").textContent = `${data.name}, here's your fuel plan`;

  document.getElementById("stat-bmr").textContent = data.bmr.toLocaleString();
  document.getElementById("stat-target").textContent = data.target_calories.toLocaleString();
  document.getElementById("stat-goal-label").textContent = `to ${data.goal_label.toLowerCase()}`;
  document.getElementById("stat-tdee").textContent = data.tdee.toLocaleString();
  document.getElementById("stat-activity-label").textContent = data.activity_label;
  document.getElementById("stat-burned").textContent = data.calories_burned_estimate.toLocaleString();

  document.getElementById("stat-bmi").textContent = data.bmi;
  document.getElementById("stat-bmi-cat").textContent = data.bmi_category;
  document.getElementById("stat-water").textContent = `${data.water_liters} L`;

  document.getElementById("gauge-target-num").textContent = data.target_calories.toLocaleString();

  renderMacroChart(data.macros);
  updateGauge(0, data.target_calories);
}

function renderMacroChart(macros) {
  const ctx = document.getElementById("macro-chart").getContext("2d");
  const values = [macros.protein_kcal, macros.carbs_kcal, macros.fat_kcal];
  const labels = ["Protein", "Carbs", "Fat"];
  const colors = [GROUP_COLORS.protein, GROUP_COLORS.carbs, GROUP_COLORS.fiber];

  if (macroChart) macroChart.destroy();
  macroChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{ data: values, backgroundColor: colors, borderWidth: 0 }],
    },
    options: {
      cutout: "68%",
      plugins: { legend: { display: false }, tooltip: { enabled: true } },
    },
  });

  const legend = document.getElementById("macro-legend");
  legend.innerHTML = "";
  const grams = [macros.protein_g, macros.carbs_g, macros.fat_g];
  labels.forEach((label, i) => {
    const li = document.createElement("li");
    li.innerHTML = `<span class="swatch" style="background:${colors[i]}"></span>${label}<span class="val">${grams[i]} g</span>`;
    legend.appendChild(li);
  });
}

// ---------------- gauge ----------------
// Semicircle arc length ~314 (radius 100, half circumference = πr ≈ 314)
function updateGauge(consumed, target) {
  document.getElementById("gauge-consumed").textContent = Math.round(consumed).toLocaleString();

  const pct = target > 0 ? Math.min(consumed / target, 1.5) : 0; // cap visual at 150%
  const arcLen = 314;
  const fillLen = Math.min(pct, 1) * arcLen;
  const fillEl = document.getElementById("gauge-fill");
  fillEl.style.strokeDashoffset = arcLen - fillLen;

  // needle sweeps -90deg (empty) to +90deg (150% of target)
  const needleDeg = -90 + (pct / 1.5) * 180;
  document.getElementById("gauge-needle").style.transform = `rotate(${needleDeg}deg)`;

  let color = "#FF6B4A"; // coral default
  if (pct > 1.0 && pct <= 1.15) color = "#E8A33D";
  if (pct > 1.15) color = "#D64545";
  fillEl.style.stroke = color;
}

// ---------------- plate builder ----------------
function setupFoodGroups(dietType) {
  document.querySelectorAll(".food-group").forEach((groupEl) => {
    const group = groupEl.dataset.group;
    const select = groupEl.querySelector(".food-select");
    select.innerHTML = "";

    const items = state.foods[group].filter(
      (f) => f.diet === "both" || f.diet === dietType
    );
    items.forEach((f) => {
      const opt = document.createElement("option");
      opt.value = f.id;
      opt.textContent = `${f.label} — ${f.unit}`;
      select.appendChild(opt);
    });
  });
}

function wirePlateBuilder() {
  document.querySelectorAll(".food-group").forEach((groupEl) => {
    const group = groupEl.dataset.group;
    const addBtn = groupEl.querySelector(".btn-add");
    addBtn.addEventListener("click", () => {
      const select = groupEl.querySelector(".food-select");
      const qtyInput = groupEl.querySelector(".food-qty");
      const foodId = select.value;
      const qty = parseFloat(qtyInput.value) || 1;
      if (!foodId || qty <= 0) return;

      const foodDef = state.foods[group].find((f) => f.id === foodId);
      if (!foodDef) return;

      state.plate.push({
        uid: `${foodId}-${Date.now()}`,
        group,
        label: foodDef.label,
        unit: foodDef.unit,
        qty,
        kcal: foodDef.kcal * qty,
        protein: foodDef.protein * qty,
        carbs: foodDef.carbs * qty,
        fat: foodDef.fat * qty,
      });
      renderPlate();
    });
  });
}

function renderPlate() {
  const tbody = document.getElementById("plate-body");
  tbody.innerHTML = "";

  if (state.plate.length === 0) {
    tbody.innerHTML = `<tr class="plate-empty"><td colspan="7">Your plate is empty — add items above.</td></tr>`;
  } else {
    state.plate.forEach((item) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="item-name">${item.label}</td>
        <td>${item.qty} × ${item.unit}</td>
        <td class="mono">${Math.round(item.kcal)}</td>
        <td class="mono">${item.protein.toFixed(1)}g</td>
        <td class="mono">${item.carbs.toFixed(1)}g</td>
        <td class="mono">${item.fat.toFixed(1)}g</td>
        <td><button class="btn-remove" data-uid="${item.uid}" title="Remove">×</button></td>
      `;
      tbody.appendChild(tr);
    });
  }

  tbody.querySelectorAll(".btn-remove").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.plate = state.plate.filter((i) => i.uid !== btn.dataset.uid);
      renderPlate();
    });
  });

  updateTotalsAndProgress();
}

function updateTotalsAndProgress() {
  if (!state.profile) return;

  const totals = state.plate.reduce(
    (acc, i) => {
      acc.kcal += i.kcal;
      acc.protein += i.protein;
      acc.carbs += i.carbs;
      acc.fat += i.fat;
      return acc;
    },
    { kcal: 0, protein: 0, carbs: 0, fat: 0 }
  );

  const { target_calories, macros } = state.profile;

  updateGauge(totals.kcal, target_calories);

  setProgress("cal", totals.kcal, target_calories, "kcal");
  setProgress("protein", totals.protein, macros.protein_g, "g");
  setProgress("carbs", totals.carbs, macros.carbs_g, "g");
  setProgress("fat", totals.fat, macros.fat_g, "g");

  const verdictEl = document.getElementById("plate-verdict");
  const pct = target_calories > 0 ? totals.kcal / target_calories : 0;
  const remaining = Math.round(target_calories - totals.kcal);

  verdictEl.classList.remove("warn", "over");
  if (state.plate.length === 0) {
    verdictEl.textContent = "Add a protein, a veggie and a carb to see how your plate stacks up against your target.";
  } else if (pct < 0.9) {
    verdictEl.textContent = `You have about ${remaining.toLocaleString()} kcal left to hit your target — try adding another item.`;
  } else if (pct <= 1.05) {
    verdictEl.textContent = `Nicely balanced — your plate is within range of your ${target_calories.toLocaleString()} kcal target.`;
  } else if (pct <= 1.2) {
    verdictEl.textContent = `You're a little over target (by ${Math.abs(remaining).toLocaleString()} kcal). Consider trimming a portion.`;
    verdictEl.classList.add("warn");
  } else {
    verdictEl.textContent = `This plate is well over your ${target_calories.toLocaleString()} kcal target (by ${Math.abs(remaining).toLocaleString()} kcal). Try reducing quantities.`;
    verdictEl.classList.add("over");
  }
}

function setProgress(key, value, target, unit) {
  const fillEl = document.getElementById(`prog-${key}`);
  const textEl = document.getElementById(`prog-${key}-text`);
  const pct = target > 0 ? Math.min((value / target) * 100, 100) : 0;
  fillEl.style.width = `${pct}%`;
  textEl.textContent = `${Math.round(value)} / ${Math.round(target)} ${unit}`;
}
