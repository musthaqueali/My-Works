// ELECTRON Broadsheet Client Application
let currentIssue = null;
let currentStreamFile = "newsletter_web_research_results.md";

document.addEventListener("DOMContentLoaded", () => {
  // Set date in masthead
  const d = new Date();
  const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
  const dateStr = d.toLocaleDateString('en-US', options).toUpperCase();
  const dateEl = document.getElementById("masthead-date");
  if (dateEl) dateEl.textContent = dateStr;

  loadInitialData();
});

async function loadInitialData() {
  await fetchStats();
  await loadCurrentIssue();
  await loadSubscribers();
  await refreshLogs();
  loadStreamFile(currentStreamFile);
}

// Navigation between Reader Landing and Editorial Studio
function switchView(view) {
  const landing = document.getElementById("view-landing");
  const admin = document.getElementById("view-admin");
  const btnLanding = document.getElementById("nav-landing-btn");
  const btnAdmin = document.getElementById("nav-admin-btn");

  if (view === "landing") {
    landing.classList.remove("hidden");
    admin.classList.add("hidden");
    btnLanding.className = "px-3.5 py-1.5 rounded-lg bg-brand-600 text-white font-semibold shadow-md shadow-brand-600/30 transition-all flex items-center gap-1.5";
    btnAdmin.className = "px-3.5 py-1.5 rounded-lg text-slate-300 hover:text-white transition-all flex items-center gap-1.5";
  } else {
    admin.classList.remove("hidden");
    landing.classList.add("hidden");
    btnAdmin.className = "px-3.5 py-1.5 rounded-lg bg-brand-600 text-white font-semibold shadow-md shadow-brand-600/30 transition-all flex items-center gap-1.5";
    btnLanding.className = "px-3.5 py-1.5 rounded-lg text-slate-300 hover:text-white transition-all flex items-center gap-1.5";
  }
}

// Editorial Studio Tab switcher
function switchAdminTab(tab) {
  const tabs = ["preview", "streams", "subscribers", "logs"];
  tabs.forEach(t => {
    const el = document.getElementById(`tab-${t}`);
    const btn = document.getElementById(`tab-btn-${t}`);
    if (!el || !btn) return;
    if (t === tab) {
      el.classList.remove("hidden");
      btn.className = "py-3 border-b-2 border-brand-500 text-white flex items-center gap-1.5 font-bold";
    } else {
      el.classList.add("hidden");
      btn.className = "py-3 border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-1.5 font-normal";
    }
  });

  if (tab === "subscribers") loadSubscribers();
  if (tab === "logs") refreshLogs();
}

// Device simulation
function setSimDevice(device) {
  const wrapper = document.getElementById("sim-frame-wrapper");
  const btnDesktop = document.getElementById("device-btn-desktop");
  const btnMobile = document.getElementById("device-btn-mobile");

  if (device === "mobile") {
    wrapper.style.maxWidth = "375px";
    btnMobile.className = "flex-1 py-1.5 bg-slate-800 text-white font-bold border border-slate-700 rounded-lg text-xs";
    btnDesktop.className = "flex-1 py-1.5 bg-slate-950 text-slate-400 font-bold border border-slate-800 rounded-lg text-xs hover:text-white";
  } else {
    wrapper.style.maxWidth = "660px";
    btnDesktop.className = "flex-1 py-1.5 bg-slate-800 text-white font-bold border border-slate-700 rounded-lg text-xs";
    btnMobile.className = "flex-1 py-1.5 bg-slate-950 text-slate-400 font-bold border border-slate-800 rounded-lg text-xs hover:text-white";
  }
}

// Fetch stats
async function fetchStats() {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();
    document.getElementById("stat-subscribers").textContent = data.active_subscribers || 0;
    document.getElementById("stat-issues").textContent = data.total_issues_sent || 0;
    const schedEl = document.getElementById("stat-scheduler");
    if (schedEl) {
      schedEl.textContent = `ACTIVE (${data.daily_send_time || '08:00 AM'})`;
    }
  } catch (err) {
    console.error("Failed to fetch stats:", err);
  }
}

// Load current issue draft
async function loadCurrentIssue() {
  try {
    const res = await fetch("/api/newsletter/current");
    const data = await res.json();
    currentIssue = data;
    document.getElementById("draft-subject").value = data.subject || "";
    document.getElementById("draft-title").value = data.title || "";
    
    // Set preview iframe content
    const iframe = document.getElementById("newsletter-preview-frame");
    const doc = iframe.contentWindow.document;
    doc.open();
    doc.write(data.html);
    doc.close();
  } catch (err) {
    console.error("Failed to load issue:", err);
  }
}

// Run Daily Automation Now (Fetches ArXiv + Updates + Sends)
async function triggerDailyRunNow() {
  if (!confirm("⚡ Execute Daily Automation Cycle now?\n\nThis will:\n1. Query live arXiv API for latest papers\n2. Compile the daily ELECTRON broadsheet\n3. Broadcast to all active subscribers via your active mailer.")) return;

  const btn = event.target;
  const origText = btn.innerHTML;
  btn.innerHTML = `<span>⏳ Querying arXiv & Sending...</span>`;
  btn.disabled = true;

  try {
    const res = await fetch("/api/scheduler/run-now", { method: "POST" });
    const data = await res.json();
    alert(`📢 ${data.message}\n\nBroadcast Results:\n- Sent: ${data.results.sent}\n- Failed: ${data.results.failed}\n- Provider: ${data.results.provider}`);
    await loadCurrentIssue();
    await fetchStats();
    await refreshLogs();
  } catch (err) {
    alert("❌ Automation run error: " + err.message);
  } finally {
    btn.innerHTML = origText;
    btn.disabled = false;
  }
}

// Trigger manual synthesis
async function triggerSynthesis() {
  const btn = event.target;
  const originalText = btn.innerHTML;
  btn.innerHTML = `<span>⏳ Synthesizing...</span>`;
  btn.disabled = true;

  try {
    const res = await fetch("/api/newsletter/generate", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      await loadCurrentIssue();
      alert("✅ ELECTRON broadsheet issue re-synthesized with live arXiv papers!");
    } else {
      alert("❌ Synthesis failed: " + data.message);
    }
  } catch (err) {
    alert("❌ Network error: " + err.message);
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}

const runSchedulerNow = triggerDailyRunNow;

// Stream file management
async function loadStreamFile(filename) {
  currentStreamFile = filename;
  document.getElementById("current-stream-filename").textContent = filename;

  document.querySelectorAll(".stream-btn").forEach(btn => {
    if (btn.getAttribute("data-file") === filename) {
      btn.className = "stream-btn w-full text-left px-3 py-2 rounded-lg text-xs font-semibold bg-brand-600 text-white shadow";
    } else {
      btn.className = "stream-btn w-full text-left px-3 py-2 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800";
    }
  });

  try {
    const res = await fetch(`/api/streams/${filename}`);
    const data = await res.json();
    document.getElementById("stream-editor").value = data.content || "";
  } catch (err) {
    console.error("Error loading stream file:", err);
  }
}

async function saveCurrentStreamFile() {
  const content = document.getElementById("stream-editor").value;
  try {
    const res = await fetch(`/api/streams/${currentStreamFile}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content })
    });
    const data = await res.json();
    if (data.success) {
      alert(`✅ Saved ${currentStreamFile} successfully!`);
    } else {
      alert("❌ Failed to save: " + data.message);
    }
  } catch (err) {
    alert("❌ Error saving file: " + err.message);
  }
}

// Subscribers management
async function loadSubscribers() {
  try {
    const res = await fetch("/api/subscribers");
    const subscribers = await res.json();
    const tbody = document.getElementById("subscribers-table-body");
    
    if (subscribers.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="px-6 py-8 text-center text-neutral-500 italic">No readers enrolled yet. Add your first subscriber above!</td></tr>`;
      return;
    }

    tbody.innerHTML = subscribers.map(sub => `
      <tr class="hover:bg-neutral-100 transition-colors">
        <td class="px-6 py-4 font-mono font-bold text-neutral-900">${sub.email}</td>
        <td class="px-6 py-4">${sub.name || '<span class="text-neutral-400">—</span>'}</td>
        <td class="px-6 py-4">
          <span class="inline-flex items-center px-2 py-0.5 text-xs font-bold ${sub.status === 'active' ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' : 'bg-rose-100 text-rose-800 border border-rose-300'}">
            ${sub.status.toUpperCase()}
          </span>
        </td>
        <td class="px-6 py-4 text-neutral-500">${sub.created_at || 'Just now'}</td>
        <td class="px-6 py-4 text-right">
          <button onclick="deleteSubscriber(${sub.id})" class="text-[#c03f13] hover:underline font-bold text-xs">Remove</button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Failed to load subscribers:", err);
  }
}

async function handlePublicSubscribe(e) {
  e.preventDefault();
  const inputEmail = document.getElementById("public-email");
  const inputName = document.getElementById("public-name");
  const feedback = document.getElementById("public-subscribe-feedback");
  const email = inputEmail.value.trim();
  const name = inputName ? inputName.value.trim() : "";

  feedback.textContent = "Transmitting enrollment...";
  feedback.className = "mt-3 font-mono text-xs text-neutral-400";

  try {
    const res = await fetch("/api/subscribe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, name })
    });
    const data = await res.json();
    if (data.success) {
      feedback.textContent = "✔ You are enrolled in the ELECTRON Daily Broadsheet!";
      feedback.className = "mt-3 font-mono text-xs text-emerald-400 font-bold";
      inputEmail.value = "";
      if (inputName) inputName.value = "";
      fetchStats();
    } else {
      feedback.textContent = data.message;
      feedback.className = "mt-3 font-mono text-xs text-amber-400";
    }
  } catch (err) {
    feedback.textContent = "Network error. Please try again.";
    feedback.className = "mt-3 font-mono text-xs text-rose-400";
  }
}

async function handleManualAddSubscriber(e) {
  e.preventDefault();
  const emailInput = document.getElementById("manual-email");
  const nameInput = document.getElementById("manual-name");

  try {
    const res = await fetch("/api/subscribe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: emailInput.value, name: nameInput.value })
    });
    const data = await res.json();
    if (data.success) {
      emailInput.value = "";
      nameInput.value = "";
      loadSubscribers();
      fetchStats();
    } else {
      alert(data.message);
    }
  } catch (err) {
    alert("Error adding subscriber: " + err.message);
  }
}

async function deleteSubscriber(id) {
  if (!confirm("Are you sure you want to remove this reader?")) return;
  try {
    const res = await fetch(`/api/subscribers/${id}`, { method: "DELETE" });
    const data = await res.json();
    if (data.success) {
      loadSubscribers();
      fetchStats();
    }
  } catch (err) {
    alert("Failed to delete: " + err.message);
  }
}

// Test Email modal
function openTestModal() {
  document.getElementById("test-email-modal").classList.remove("hidden");
}

function closeTestModal() {
  document.getElementById("test-email-modal").classList.add("hidden");
}

async function dispatchTestEmail() {
  const email = document.getElementById("test-email-input").value.trim();
  if (!email) return alert("Please enter a valid email.");

  const subject = document.getElementById("draft-subject").value;
  try {
    const res = await fetch("/api/newsletter/test-send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, subject })
    });
    const data = await res.json();
    closeTestModal();
    alert(data.message);
    refreshLogs();
  } catch (err) {
    alert("Test dispatch failed: " + err.message);
  }
}

// Broadcast to All
async function confirmBroadcast() {
  if (!confirm("Are you sure you want to broadcast today's ELECTRON edition to ALL active subscribers?")) return;

  const subject = document.getElementById("draft-subject").value;
  try {
    const res = await fetch("/api/newsletter/broadcast", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ subject })
    });
    const data = await res.json();
    alert(`📢 Transmission Report:\n- Total: ${data.total}\n- Sent: ${data.sent}\n- Failed: ${data.failed}\n- Provider: ${data.provider}`);
    fetchStats();
    refreshLogs();
  } catch (err) {
    alert("Broadcast error: " + err.message);
  }
}

// Refresh Delivery Logs
async function refreshLogs() {
  try {
    const res = await fetch("/api/logs");
    const logs = await res.json();
    const container = document.getElementById("delivery-logs-container");
    if (logs.length === 0) {
      container.innerHTML = `<div class="text-neutral-500 italic">No transmissions logged yet.</div>`;
      return;
    }
    container.innerHTML = logs.map(l => `<div class="py-0.5">${l}</div>`).join("");
  } catch (err) {
    console.error("Failed to load logs:", err);
  }
}

// Settings handlers
function onProviderChange(provider) {
  const smtpSec = document.getElementById("section-smtp-settings");
  const resendSec = document.getElementById("section-resend-settings");

  if (provider === "smtp") {
    smtpSec.classList.remove("hidden");
    resendSec.classList.add("hidden");
  } else if (provider === "resend") {
    resendSec.classList.remove("hidden");
    smtpSec.classList.add("hidden");
  } else {
    smtpSec.classList.add("hidden");
    resendSec.classList.add("hidden");
  }
}

async function loadSettings() {
  try {
    const res = await fetch("/api/settings");
    const s = await res.json();
    
    const radios = document.querySelectorAll('input[name="provider_radio"]');
    radios.forEach(r => {
      r.checked = (r.value === s.email_provider);
    });
    onProviderChange(s.email_provider);

    document.getElementById("set-from-email").value = s.from_email || "";
    document.getElementById("set-from-name").value = s.from_name || "ELECTRON Gazette";
    document.getElementById("set-smtp-host").value = s.smtp_host || "smtp.gmail.com";
    document.getElementById("set-smtp-port").value = s.smtp_port || 587;
    document.getElementById("set-smtp-user").value = s.smtp_user || "";
    if (s.smtp_password_set) {
      document.getElementById("set-smtp-password").placeholder = "•••••••••••••••• (Password configured)";
    }
  } catch (err) {
    console.error("Failed to load settings:", err);
  }
}

async function saveEmailSettings(e) {
  e.preventDefault();
  const provider = document.querySelector('input[name="provider_radio"]:checked').value;
  const fromEmail = document.getElementById("set-from-email").value.trim();
  const fromName = document.getElementById("set-from-name").value.trim();
  const smtpHost = document.getElementById("set-smtp-host").value.trim();
  const smtpPort = parseInt(document.getElementById("set-smtp-port").value) || 587;
  const smtpUser = document.getElementById("set-smtp-user").value.trim();
  const smtpPassword = document.getElementById("set-smtp-password").value.trim();
  const resendKey = document.getElementById("set-resend-key").value.trim();
  const statusMsg = document.getElementById("settings-status-msg");

  statusMsg.textContent = "Saving...";
  statusMsg.className = "text-neutral-600 font-mono text-xs";

  try {
    const res = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email_provider: provider,
        from_email: fromEmail,
        from_name: fromName,
        smtp_host: smtpHost,
        smtp_port: smtpPort,
        smtp_user: smtpUser,
        smtp_password: smtpPassword,
        resend_api_key: resendKey
      })
    });
    const data = await res.json();
    if (data.success) {
      statusMsg.textContent = "✔ " + data.message;
      statusMsg.className = "text-emerald-700 font-bold font-mono text-xs";
      fetchStats();
    } else {
      statusMsg.textContent = "❌ " + data.message;
      statusMsg.className = "text-rose-700 font-bold font-mono text-xs";
    }
  } catch (err) {
    statusMsg.textContent = "❌ Error: " + err.message;
    statusMsg.className = "text-rose-700 font-bold font-mono text-xs";
  }
}
