const simulations = {
  healthy: {
    status: "PASS · CLEAR",
    explanation: "The response satisfies the hard contract and raises no statistical review signal.",
    claim: "This controlled response satisfies protocol version 1.0.0.",
  },
  schema: {
    status: "FAIL · CLEAR",
    explanation: "A required field is absent. Downstream meaning can no longer be reconstructed safely.",
    claim: "The response violates the declared schema contract.",
  },
  identity: {
    status: "FAIL · CLEAR",
    explanation: "The series denominator changed. A valid number would now describe a different quantity.",
    claim: "The response no longer represents the pinned series identity.",
  },
  late: {
    status: "FAIL · CLEAR",
    explanation: "After the grace period, the latest expected TARGET-day observation is missing.",
    claim: "The response violates the predeclared freshness contract at this check time.",
  },
  spike: {
    status: "PASS · REVIEW",
    explanation: "Structure and freshness remain valid, but the synthetic latest return crosses the robust review threshold.",
    claim: "The observation warrants inspection; the signal alone does not establish an error.",
  },
};

const $ = (selector) => document.querySelector(selector);

for (const input of document.querySelectorAll('input[name="fault"]')) {
  input.addEventListener("change", () => {
    const item = simulations[input.value];
    $("#sim-status").textContent = item.status;
    $("#sim-explanation").textContent = item.explanation;
    $("#sim-claim").textContent = item.claim;
  });
}

/* theme toggle: the only browser storage this site uses */
const root = document.documentElement;
const toggle = $("#theme-toggle");
const syncToggle = () => {
  const dark = root.dataset.theme === "dark";
  toggle.setAttribute("aria-label", dark ? "Switch to light theme" : "Switch to dark theme");
};
syncToggle();
toggle.addEventListener("click", () => {
  root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
  try {
    localStorage.setItem("theme", root.dataset.theme);
  } catch (error) {
    /* storage unavailable: the choice lasts for this visit only */
  }
  syncToggle();
});

/* entrances play once; content is visible without JavaScript */
const risers = document.querySelectorAll(".rise");
if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add("in");
          observer.unobserve(entry.target);
        }
      }
    },
    { threshold: 0.12 },
  );
  risers.forEach((node) => observer.observe(node));
} else {
  risers.forEach((node) => node.classList.add("in"));
}

const formatDate = (value) =>
  value
    ? new Intl.DateTimeFormat("en-GB", {
        dateStyle: "medium",
        timeStyle: value.includes("T") ? "short" : undefined,
      }).format(new Date(value))
    : "—";

fetch("data/latest.json")
  .then((response) => {
    if (!response.ok) throw new Error("No recorded run");
    return response.json();
  })
  .then((report) => {
    const contract = report.contract_status.toUpperCase();
    const review = report.review_status.toUpperCase();
    $("#contract-status").textContent = contract;
    $("#review-status").textContent = review;
    $("#latest-date").textContent = report.latest_observation;
    $("#row-count").textContent = report.observation_count;
    $("#checked-at").textContent = formatDate(report.checked_at);
    $("#live-note").textContent = report.findings.length
      ? report.findings.map((item) => item.message).join(" ")
      : "No findings were emitted by the latest recorded run.";
  })
  .catch(() => {
    $("#contract-status").textContent = "—";
    $("#review-status").textContent = "—";
    $("#live-note").textContent =
      "No complete live run has been recorded yet; the deterministic validation lab remains available.";
  });

fetch("data/evidence-index.json")
  .then((response) => (response.ok ? response.json() : Promise.reject()))
  .then((index) => {
    $("#prospective-runs").textContent = index.prospective_run_count;
  })
  .catch(() => {});

/* alarm audit chart, drawn from the committed post-hoc audit file; the table in the page holds the same numbers */
const SVG = "http://www.w3.org/2000/svg";
const element = (name, attributes, text) => {
  const node = document.createElementNS(SVG, name);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  return node;
};

fetch("data/threshold-audit.json")
  .then((response) => (response.ok ? response.json() : Promise.reject()))
  .then((audit) => {
    const svg = $("#alarm-chart");
    const left = 150;
    const right = 690;
    const top = 16;
    const rowHeight = 54;
    const low = -7;
    const high = -1;
    const x = (rate) => left + ((Math.log10(Math.max(rate, 10 ** low)) - low) / (high - low)) * (right - left);
    for (let exponent = low; exponent <= high; exponent += 1) {
      const position = x(10 ** exponent);
      svg.appendChild(element("line", { x1: position, x2: position, y1: top, y2: top + rowHeight * audit.thresholds.length, class: "grid-line" }));
      const labels = { "-7": "1 in 10M", "-6": "1 in 1M", "-5": "1 in 100k", "-4": "1 in 10k", "-3": "0.1%", "-2": "1%", "-1": "10%" };
      const label = labels[exponent];
      svg.appendChild(element("text", { x: position, y: top + rowHeight * audit.thresholds.length + 24, "text-anchor": "middle" }, label));
    }
    audit.thresholds.forEach((row, index) => {
      const y = top + rowHeight * index + rowHeight / 2;
      const strong = row.threshold === 6;
      svg.appendChild(element("text", { x: left - 16, y: y + 5, "text-anchor": "end", class: strong ? "label-strong" : "" }, `z ≥ ${row.threshold}`));
      const expected = row.gaussian_expected_signals / audit.evaluated_days;
      svg.appendChild(element("line", { x1: x(expected), x2: x(row.rate), y1: y, y2: y, stroke: "var(--ink-3)", "stroke-width": 2, opacity: 0.35 }));
      svg.appendChild(element("circle", { cx: x(expected), cy: y, r: 8, class: "bar-model" }));
      svg.appendChild(element("circle", { cx: x(row.rate), cy: y, r: 9, class: "bar-real" }));
    });
  })
  .catch(() => {
    $("#alarm-chart").setAttribute("hidden", "");
  });
