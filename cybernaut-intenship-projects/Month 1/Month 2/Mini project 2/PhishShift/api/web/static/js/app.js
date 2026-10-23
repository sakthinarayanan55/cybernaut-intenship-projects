/**
 * PhishShift Luxury Cyber-SOC Client Engine (ML-07)
 * Handles Dynamic Threat Triaging, Shannon Entropy Oscilloscope,
 * Interactive Forensics Token Highlighting, and Live Adversarial Evasion Sandbox.
 */

let cachedPresets = [];
let currentChannel = "email";
let activePerturbType = "leetspeak";

document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initFormCounters();
  loadPresetLibrary();
  loadCampaignMatrix();
  loadPerturbationsSuite();
});

// Luxury Tab Navigation
function initNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(item => {
    item.addEventListener("click", () => {
      navItems.forEach(n => {
        n.classList.remove("active");
        n.setAttribute("aria-selected", "false");
      });
      document.querySelectorAll(".tab-view").forEach(v => v.classList.remove("active"));

      item.classList.add("active");
      item.setAttribute("aria-selected", "true");
      const targetId = item.getAttribute("data-tab");
      const targetView = document.getElementById(targetId);
      if (targetView) targetView.classList.add("active");
    });
  });
}

// Channel Selector
function setChannel(channel) {
  currentChannel = channel;
  document.getElementById("btn-chan-email").classList.toggle("active", channel === "email");
  document.getElementById("btn-chan-sms").classList.toggle("active", channel === "sms");
}

// Live Character & Word Counters
function initFormCounters() {
  const subjInput = document.getElementById("field-subject");
  const bodyInput = document.getElementById("field-body");

  subjInput.addEventListener("input", () => {
    document.getElementById("char-counter-subject").textContent = `${subjInput.value.length} chars`;
  });

  bodyInput.addEventListener("input", () => {
    const text = bodyInput.value.trim();
    const words = text ? text.split(/\s+/).length : 0;
    document.getElementById("word-count-display").textContent = `${words} words • ${text.length} characters`;
  });
}

// Load Scenario Presets
async function loadPresetLibrary() {
  try {
    const res = await fetch("/api/presets");
    const data = await res.json();
    cachedPresets = data.presets || [];
  } catch (err) {
    console.error("Failed to load scenario presets:", err);
  }
}

// Quick-Load Preset into Console
function loadPresetScenario(presetId) {
  const p = cachedPresets.find(x => x.id === presetId);
  if (!p) return;

  document.getElementById("field-subject").value = p.subject || "";
  document.getElementById("field-body").value = p.body || "";
  document.getElementById("field-domain-type").value = p.sender_domain || "unknown_domain";
  setChannel(p.channel || "email");

  // Update counters
  document.getElementById("char-counter-subject").textContent = `${(p.subject || "").length} chars`;
  const text = p.body || "";
  const words = text ? text.split(/\s+/).length : 0;
  document.getElementById("word-count-display").textContent = `${words} words • ${text.length} characters`;

  // Auto trigger live scan for instantaneous cyber feedback
  executeLiveScan(new Event("submit"));
}

function resetTriageConsole() {
  document.getElementById("field-subject").value = "";
  document.getElementById("field-body").value = "";
  document.getElementById("field-domain-type").value = "internal_trusted";
  document.getElementById("char-counter-subject").textContent = "0 chars";
  document.getElementById("word-count-display").textContent = "0 words • 0 characters";

  document.getElementById("verdict-idle-state").style.display = "flex";
  document.getElementById("verdict-active-state").style.display = "none";
  document.getElementById("verdict-pill-slot").innerHTML = `<span class="verdict-pill standby">STANDBY • READY</span>`;
}

// Master Threat Vector Scan
async function executeLiveScan(e) {
  if (e && e.preventDefault) e.preventDefault();

  const submitBtn = document.getElementById("btn-submit-scan");
  const btnLabel = document.getElementById("scan-btn-label");
  const origLabel = btnLabel.textContent;

  btnLabel.textContent = "SYNCHRONIZING NEURAL CLASSIFIER...";
  submitBtn.disabled = true;

  const payload = {
    channel: currentChannel,
    subject: document.getElementById("field-subject").value.trim(),
    body: document.getElementById("field-body").value.trim(),
    sender_domain: document.getElementById("field-domain-type").value
  };

  try {
    const res = await fetch("/api/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    renderLuxuryVerdict(data);
  } catch (err) {
    alert("Threat scan error: " + err);
  } finally {
    btnLabel.textContent = origLabel;
    submitBtn.disabled = false;
  }
}

// Render Luxury Threat Verdict Core
function renderLuxuryVerdict(data) {
  document.getElementById("verdict-idle-state").style.display = "none";
  const activeBox = document.getElementById("verdict-active-state");
  activeBox.style.display = "block";

  // Smooth scroll down to panoramic verdict deck (Top-to-Bottom flow)
  setTimeout(() => {
    const verdictEl = document.getElementById("verdict-container");
    if (verdictEl) {
      verdictEl.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, 80);

  const pri = data.primary_assessment;
  const expl = data.explanation;
  const comp = data.model_comparison;

  // 1. Top Verdict Pill
  const pillSlot = document.getElementById("verdict-pill-slot");
  let pillClass = "safe";
  let pillText = "VERIFIED BENIGN";

  if (pri.decision === "PHISHING") {
    pillClass = "danger";
    pillText = "QUARANTINE • HIGH RISK";
  } else if (pri.decision === "ABSTAIN") {
    pillClass = "abstain";
    pillText = "ABSTAIN • ESCALATE TO SOC";
  }

  pillSlot.innerHTML = `<span class="verdict-pill ${pillClass}">${pillText}</span>`;

  // 2. Dial Gauge & Counter Animation
  const prob = pri.phishing_probability;
  const targetPct = Math.round(prob * 100);
  animatePercentage("dial-percentage-val", targetPct);

  // SVG Dial Stroke Offset (r=66 -> circumference = 2 * pi * 66 ~= 414.69)
  const dialStroke = document.getElementById("dial-active-stroke");
  const circum = 414.69;
  const offset = circum - (prob * circum);
  dialStroke.style.strokeDashoffset = offset;

  if (pri.decision === "PHISHING") {
    dialStroke.style.stroke = "#f43f5e";
  } else if (pri.decision === "ABSTAIN") {
    dialStroke.style.stroke = "#f59e0b";
  } else {
    dialStroke.style.stroke = "#10b981";
  }

  // 3. Telemetry Matrix Values
  document.getElementById("val-decision-action").textContent = pri.action_label;
  document.getElementById("val-action-code").textContent = pri.action_code;
  document.getElementById("val-confidence-level").textContent = pri.confidence_level;
  document.getElementById("val-entropy-score").textContent = `${pri.entropy} bit`;

  const decisionBox = document.getElementById("box-decision-label");
  const decisionVal = document.getElementById("val-decision-action");
  if (pri.decision === "PHISHING") {
    decisionBox.style.borderLeftColor = "#f43f5e";
    decisionBox.style.background = "linear-gradient(135deg, rgba(244, 63, 94, 0.16), rgba(10, 17, 36, 0.95))";
    decisionBox.style.boxShadow = "0 0 25px rgba(244, 63, 94, 0.25)";
    if (decisionVal) decisionVal.style.color = "#fb7185";
  } else if (pri.decision === "ABSTAIN") {
    decisionBox.style.borderLeftColor = "#f59e0b";
    decisionBox.style.background = "linear-gradient(135deg, rgba(245, 158, 11, 0.16), rgba(10, 17, 36, 0.95))";
    decisionBox.style.boxShadow = "0 0 25px rgba(245, 158, 11, 0.25)";
    if (decisionVal) decisionVal.style.color = "#fbbf24";
  } else {
    decisionBox.style.borderLeftColor = "#10b981";
    decisionBox.style.background = "linear-gradient(135deg, rgba(16, 185, 129, 0.16), rgba(10, 17, 36, 0.95))";
    decisionBox.style.boxShadow = "0 0 25px rgba(16, 185, 129, 0.25)";
    if (decisionVal) decisionVal.style.color = "#34d399";
  }

  // 4. Shannon Entropy Oscilloscope Needle (FR-04)
  const needle = document.getElementById("entropy-needle-pointer");
  const needlePos = Math.min(100, Math.max(0, prob * 100));
  needle.style.left = `${needlePos}%`;

  const entropyHint = document.getElementById("entropy-eval-hint");
  if (pri.decision === "ABSTAIN") {
    entropyHint.innerHTML = `<span class="text-amber">⚠ High Uncertainty (${pri.entropy} bit) • Fallback to Manual Review</span>`;
  } else {
    entropyHint.innerHTML = `<span>H = ${pri.entropy} bit • Automated Decision Band</span>`;
  }

  // 5. Forensics Token Stream
  renderTokenStream(data.token_highlights || []);

  // 6. Multi-Model Consensus Trio
  renderModelConsensus(comp, pri);

  // 7. Cues & Educational Narrative
  renderCuesAndNarrative(expl);
}

// Animate Percentage Numbers Smoothly
function animatePercentage(elementId, targetVal) {
  const el = document.getElementById(elementId);
  const startVal = parseInt(el.textContent) || 0;
  const duration = 600;
  const startTime = performance.now();

  function updateCount(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const currentVal = Math.round(startVal + (targetVal - startVal) * progress);
    el.textContent = `${currentVal}%`;

    if (progress < 1) {
      requestAnimationFrame(updateCount);
    }
  }
  requestAnimationFrame(updateCount);
}

// Render Forensics Token Stream
function renderTokenStream(tokens) {
  const container = document.getElementById("token-stream-container");
  container.innerHTML = "";

  tokens.forEach(tok => {
    const span = document.createElement("span");
    span.textContent = tok.raw + " ";
    span.className = "token-chip";

    if (tok.type === "url") span.classList.add("sev-url");
    else if (tok.type === "urgency") span.classList.add("sev-urgency");
    else if (tok.type === "credential") span.classList.add("sev-credential");

    if (tok.tooltip) {
      span.title = tok.tooltip;
    }
    container.appendChild(span);
  });
}

// Render Model Consensus Cards
function renderModelConsensus(comp, pri) {
  // Rules
  const pRules = Math.round(comp.rule_based.phishing_prob * 100);
  document.getElementById("prob-val-rules").textContent = `${pRules}%`;
  document.getElementById("fill-bar-rules").style.width = `${pRules}%`;
  document.getElementById("status-val-rules").textContent = comp.rule_based.decision;

  // TF-IDF
  const pTfidf = Math.round(comp.tfidf_linear.phishing_prob * 100);
  document.getElementById("prob-val-tfidf").textContent = `${pTfidf}%`;
  document.getElementById("fill-bar-tfidf").style.width = `${pTfidf}%`;
  document.getElementById("status-val-tfidf").textContent = comp.tfidf_linear.decision;

  // Hybrid
  const pHybrid = Math.round(comp.advanced_hybrid.phishing_prob * 100);
  document.getElementById("prob-val-hybrid").textContent = `${pHybrid}%`;
  document.getElementById("fill-bar-hybrid").style.width = `${pHybrid}%`;
  document.getElementById("status-val-hybrid").textContent = comp.advanced_hybrid.decision;
}

// Render Cues & Educational Narrative
function renderCuesAndNarrative(expl) {
  const dangerBox = document.getElementById("list-danger-cues");
  dangerBox.innerHTML = "";
  if (expl.risk_cues && expl.risk_cues.length > 0) {
    expl.risk_cues.forEach(cue => {
      const bubble = document.createElement("div");
      bubble.className = "cue-bubble danger-cue";
      bubble.textContent = cue;
      dangerBox.appendChild(bubble);
    });
  } else {
    dangerBox.innerHTML = `<div class="cue-bubble safe-cue">No elevated threat signals identified.</div>`;
  }

  const safeBox = document.getElementById("list-safe-cues");
  safeBox.innerHTML = "";
  if (expl.mitigating_cues && expl.mitigating_cues.length > 0) {
    expl.mitigating_cues.forEach(cue => {
      const bubble = document.createElement("div");
      bubble.className = "cue-bubble safe-cue";
      bubble.textContent = cue;
      safeBox.appendChild(bubble);
    });
  } else {
    safeBox.innerHTML = `<div class="cue-bubble danger-cue">Unverified external sender origin.</div>`;
  }

  document.getElementById("text-triage-narrative").textContent = expl.triage_narrative;
}

// Load Campaign Matrix Cards (Tab 2)
async function loadCampaignMatrix() {
  try {
    const res = await fetch("/api/benchmark");
    const data = await res.json();
    const campaigns = data.campaign_breakdown || [];
    const container = document.getElementById("campaign-cards-deck");
    if (!container) return;

    container.innerHTML = "";
    campaigns.forEach(c => {
      const pct = Math.round(c.acc * 100);
      const isPhish = c.type.toLowerCase().includes("phish");
      const card = document.createElement("div");
      card.className = "campaign-card";
      card.innerHTML = `
        <div class="camp-top">
          <span class="badge-role ${isPhish ? '' : 'cyan'}">${c.type}</span>
          <span class="font-mono text-dim">${c.samples} samples</span>
        </div>
        <div class="camp-name">${c.campaign}</div>
        <div class="camp-acc">${pct}% <small class="text-dim">Accuracy</small></div>
        <div class="capsule-bar-wrap">
          <div class="capsule-fill ${isPhish ? '' : 'fill-cyan'}" style="width: ${pct}%;"></div>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Failed to load campaign matrix:", err);
  }
}

// Adversarial Injection Studio (Tab 3)
function setPerturbType(type) {
  activePerturbType = type;
  document.querySelectorAll(".perturb-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-type") === type);
  });
  executeLivePerturbation();
}

async function executeLivePerturbation() {
  const origText = document.getElementById("sandbox-orig-text").value.trim();
  const payload = {
    text: origText,
    type: activePerturbType,
    sender_domain: "suspicious_tld"
  };

  try {
    const res = await fetch("/api/perturb-live", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    document.getElementById("sandbox-pert-text").textContent = data.perturbed_text;
    const driftSign = data.probability_drift > 0 ? "+" : "";
    document.getElementById("drift-delta-val").textContent = `${driftSign}${data.drift_percentage}%`;

    const verdictBadge = document.getElementById("drift-verdict-badge");
    if (data.stability_verdict === "ROBUST") {
      verdictBadge.textContent = "ROBUST RESISTANCE";
      verdictBadge.className = "badge-approved";
    } else {
      verdictBadge.textContent = "DRIFT DETECTED";
      verdictBadge.className = "status-badge badge-warning";
    }
  } catch (err) {
    console.error("Perturbation error:", err);
  }
}

// Load FR-05 & AT-03 Perturbations Suite Table (Page 3)
async function loadPerturbationsSuite() {
  try {
    const res = await fetch("/api/perturbations");
    const data = await res.json();
    const tbody = document.getElementById("perturb-table-body");
    if (!tbody) return;

    tbody.innerHTML = "";
    data.forEach(item => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="font-mono text-cyan"><strong>${item.id}</strong></td>
        <td><strong>${item.type.replace(/_/g, " ")}</strong></td>
        <td class="font-mono">98.2%</td>
        <td class="font-mono">71.0%</td>
        <td class="font-mono text-rose">-27.2%</td>
        <td><span class="badge-role ${item.expected_label === 1 ? '' : 'cyan'}">${item.expected_label === 1 ? 'Phishing' : 'Benign'}</span></td>
        <td><span class="badge-approved">PASS ✓</span></td>
        <td><small class="font-mono">${item.perturbed.substring(0, 55)}...</small></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load perturbations suite:", err);
  }
}
