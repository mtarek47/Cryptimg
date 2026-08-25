// Stegstr Web Dashboard Controller — Terminal Console Edition

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  loadStatus();
  loadFeed();
  loadRelays();
  setupFeedHandlers();
  setupRelayHandlers();
  setupEmbedHandlers();
  setupDetectHandlers();
  setupDiagnosticsHandlers();
  setupMessagesHandlers();
  setupCopyNpubHandler();
  loadDMInbox();
});

function initTabs() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(item => {
    item.addEventListener("click", () => {
      const targetTab = item.getAttribute("data-tab");
      switchTab(targetTab);
    });
  });
}

function switchTab(tabId) {
  document.querySelectorAll(".nav-item").forEach(i => i.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

  const navItem = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
  const content = document.getElementById(tabId);

  if (navItem) navItem.classList.add("active");
  if (content) content.classList.add("active");

  if (tabId === "tab-messages") {
    loadDMInbox();
  } else if (tabId === "tab-feed") {
    loadFeed();
  } else if (tabId === "tab-relays") {
    loadRelays();
  }
}

async function loadStatus() {
  try {
    const res = await fetch("/api/v1/status");
    const data = await res.json();
    if (data.identity) {
      document.getElementById("display-npub").innerText = data.identity.npub;
    }
  } catch (err) {
    console.error("Status load failed", err);
  }
}

async function loadFeed() {
  const container = document.getElementById("feed-posts-list");
  try {
    const res = await fetch("/api/v1/feed");
    const posts = await res.json();

    if (!posts || posts.length === 0) {
      container.innerHTML = `<div class="card"><p style="color:var(--text-muted);">[SYS_LOG] No posts found in timeline. Create one!</p></div>`;
      return;
    }

    container.innerHTML = posts.map(p => {
      const displayMsg = p.decrypted_content || p.content;
      return `
        <div class="card">
          <div style="font-size:11px; color:var(--term-cyan); margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
            <span>From: <code>${p.pubkey.substring(0, 16)}...</code> | ${new Date(p.created_at * 1000).toLocaleString()}</span>
            ${p.is_dm ? `<span class="badge badge-success" style="float:right;">🔒 ENCRYPTED DM (KIND 4)</span>` : ''}
          </div>
          <p style="color:var(--term-green); font-size:14px; margin-top:6px;">${displayMsg}</p>
          ${p.carrier_path ? `<div style="margin-top:10px;"><small class="badge badge-success">🖼️ STEGANOGRAPHIC CARRIER ATTACHED</small></div>` : ''}
        </div>
      `;
    }).join("");

  } catch (err) {
    container.innerHTML = `<div class="card"><p style="color:var(--term-red);">[SYS_ERR] Failed to load timeline feed.</p></div>`;
  }
}

function setupFeedHandlers() {
  const pubBtn = document.getElementById("btn-publish-note");
  if (!pubBtn) return;

  pubBtn.addEventListener("click", async () => {
    const textInput = document.getElementById("feed-post-text");
    const text = textInput.value.trim();
    if (!text) {
      alert("Please enter a note to publish.");
      return;
    }

    try {
      const res = await fetch("/api/v1/posts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      const data = await res.json();
      if (data.status === "CREATED") {
        textInput.value = "";
        loadFeed();
      } else {
        alert("Failed to publish note: " + (data.error || "Unknown error"));
      }
    } catch (err) {
      alert("Publish request failed: " + err);
    }
  });
}

async function loadDMInbox() {
  const container = document.getElementById("dm-inbox-container");
  if (!container) return;

  try {
    const res = await fetch("/api/v1/messages");
    const messages = await res.json();

    if (!messages || messages.length === 0) {
      container.innerHTML = `<p style="color:var(--text-muted); font-size:13px;">[SYS_LOG] No direct messages sent or received yet.</p>`;
      return;
    }

    container.innerHTML = messages.map(m => {
      const recipientTag = m.tags && m.tags.length > 0 ? m.tags[0][1] : 'Unknown';
      const text = m.decrypted_text || m.content;
      const statusBadge = m.decrypted_success 
        ? `<span class="badge badge-success">🔒 E2EE DECRYPTED</span>` 
        : `<span class="badge badge-error">🔐 ENCRYPTED FOR RECIPIENT</span>`;

      return `
        <div style="background:#000; border:1px solid var(--border-color); border-radius:6px; padding:12px; margin-bottom:12px;">
          <div style="font-size:11px; color:var(--text-muted); margin-bottom:6px; display:flex; justify-content:space-between; align-items:center;">
            <span>Sender: <code style="color:var(--term-cyan);">${m.pubkey.substring(0, 16)}...</code> | Recipient: <code style="color:var(--term-amber);">${recipientTag.substring(0, 16)}...</code></span>
            ${statusBadge}
          </div>
          <p style="color:var(--term-green); font-size:13px; font-weight:500;">${text}</p>
          <div style="font-size:10px; color:var(--text-muted); margin-top:6px; text-align:right;">
            Event ID: <code>${m.id.substring(0, 16)}...</code> | ${new Date(m.created_at * 1000).toLocaleString()}
          </div>
        </div>
      `;
    }).join("");

  } catch (err) {
    container.innerHTML = `<p style="color:var(--term-red); font-size:13px;">[SYS_ERR] Failed to load DM inbox.</p>`;
  }
}

async function loadRelays() {
  const tbody = document.getElementById("relay-table-body");
  try {
    const res = await fetch("/api/v1/relays");
    const relays = await res.json();
    tbody.innerHTML = relays.map(r => `
      <tr>
        <td><code>${r.url}</code></td>
        <td><span class="badge ${r.status === 'ONLINE' ? 'badge-success' : 'badge-error'}">${r.status}</span></td>
        <td>${r.latency_ms > 0 ? r.latency_ms + ' ms' : '--'}</td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="3">Failed to load relays.</td></tr>`;
  }
}

function setupRelayHandlers() {
  const btn = document.getElementById("btn-test-relays");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    btn.disabled = true;
    btn.innerText = "⚡ TESTING RELAYS...";
    try {
      await fetch("/api/v1/relays/test", { method: "POST" });
      await loadRelays();
    } catch (err) {
      console.error("Relay test error:", err);
    } finally {
      btn.disabled = false;
      btn.innerText = "⚡ TEST ALL RELAYS";
    }
  });
}

function setupEmbedHandlers() {
  const dropzone = document.getElementById("embed-dropzone");
  const fileInput = document.getElementById("embed-file-input");
  const messageInput = document.getElementById("embed-message-text");
  let selectedFile = null;

  dropzone.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      selectedFile = e.target.files[0];
      showEmbedPreview(selectedFile);
    }
  });

  document.getElementById("btn-embed-action").addEventListener("click", async () => {
    if (!selectedFile) {
      alert("Please select a cover carrier image first.");
      return;
    }
    const text = messageInput.value.trim();
    if (!text) {
      alert("Please enter a message payload.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("message", text);
    formData.append("robustness", document.getElementById("embed-robustness").value);

    try {
      const res = await fetch("/api/v1/encode", { method: "POST", body: formData });
      const data = await res.json();

      if (data.status === "SUCCESS") {
        document.getElementById("embed-result-card").style.display = "block";
        document.getElementById("res-codec").innerText = data.codec;
        document.getElementById("res-psnr").innerText = `${data.psnr_db} dB`;
        document.getElementById("res-ssim").innerText = data.ssim;
        
        const link = document.getElementById("res-download-link");
        link.href = data.stego_image_base64;
        link.download = `stego_${selectedFile.name}`;
      } else {
        alert("Encoding failed: " + (data.error || "Unknown error"));
      }
    } catch (err) {
      alert("Embedding request failed: " + err);
    }
  });
}

function showEmbedPreview(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    document.getElementById("embed-preview-img").src = e.target.result;
    document.getElementById("embed-preview-container").style.display = "block";
    document.querySelector("#embed-dropzone .dropzone-text").style.display = "none";
  };
  reader.readAsDataURL(file);
}

function setupDetectHandlers() {
  const dropzone = document.getElementById("detect-dropzone");
  const fileInput = document.getElementById("detect-file-input");

  dropzone.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", async (e) => {
    if (e.target.files.length > 0) {
      const file = e.target.files[0];
      const formData = new FormData();
      formData.append("file", file);

      try {
        const res = await fetch("/api/v1/decode", { method: "POST", body: formData });
        const data = await res.json();

        const card = document.getElementById("detect-results-card");
        const badge = document.getElementById("detect-status-badge");
        const details = document.getElementById("detect-output-details");
        card.style.display = "block";

        if (data.status === "FOUND") {
          badge.className = "badge badge-success";
          badge.innerText = "✅ STEGSTR PAYLOAD FOUND";
          details.innerHTML = `
            <p style="margin-bottom:6px;"><strong>Codec:</strong> ${data.codec}</p>
            <p style="margin-bottom:6px;"><strong>Sender:</strong> <code style="color:var(--term-cyan);">${data.sender || 'Unknown'}</code></p>
            <p style="color:var(--term-green); margin-bottom:6px;"><strong>Message:</strong> ${data.message || 'Binary Payload'}</p>
          `;
        } else {
          badge.className = "badge badge-error";
          badge.innerText = "❌ NO PAYLOAD DETECTED";
          details.innerHTML = `<p style="color:var(--text-muted);">No Stegstr payload was found inside this image.</p>`;
        }

      } catch (err) {
        alert("Detection request failed: " + err);
      }
    }
  });
}

function setupDiagnosticsHandlers() {
  const fileInput = document.getElementById("benchmark-file-input");
  const runBtn = document.getElementById("btn-run-benchmark");

  if (!runBtn) return;

  runBtn.addEventListener("click", async () => {
    if (!fileInput.files || fileInput.files.length === 0) {
      alert("Please select an image file to run the robustness benchmark.");
      return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    runBtn.disabled = true;
    runBtn.innerText = "⏳ EXECUTING BENCHMARK SUITE...";

    try {
      const res = await fetch("/api/v1/benchmark", { method: "POST", body: formData });
      const data = await res.json();

      document.getElementById("benchmark-results-container").style.display = "block";
      document.getElementById("benchmark-score").innerText = `${data.overall_robustness}%`;

      const tableContainer = document.getElementById("benchmark-metrics-table");
      let html = `<table class="relay-table" style="margin-top:15px;">
        <thead>
          <tr>
            <th>TRANSFORMATION PIPELINE</th>
            <th>RESULT</th>
            <th>BIT ERROR RATE (BER)</th>
          </tr>
        </thead>
        <tbody>`;

      for (const [key, val] of Object.entries(data.transformations)) {
        html += `<tr>
          <td><code>${key}</code></td>
          <td><span class="badge ${val.pass ? 'badge-success' : 'badge-error'}">${val.status}</span></td>
          <td>${val.ber}</td>
        </tr>`;
      }

      html += `</tbody></table>`;
      tableContainer.innerHTML = html;

    } catch (err) {
      alert("Benchmark execution failed: " + err);
    } finally {
      runBtn.disabled = false;
      runBtn.innerText = "🚀 EXECUTE BENCHMARK SUITE";
    }
  });
}

function setupMessagesHandlers() {
  const sendBtn = document.getElementById("btn-send-dm");
  const refreshBtn = document.getElementById("btn-refresh-dms");

  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => loadDMInbox());
  }

  if (!sendBtn) return;

  sendBtn.addEventListener("click", async () => {
    const recipient = document.getElementById("dm-recipient").value.trim();
    const text = document.getElementById("dm-text").value.trim();

    if (!recipient) {
      alert("Please enter recipient's npub or hex public key.");
      return;
    }
    if (!text) {
      alert("Please enter direct message text.");
      return;
    }

    try {
      const res = await fetch("/api/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ recipient, text })
      });
      const data = await res.json();

      if (data.status === "CREATED") {
        alert(`✅ Encrypted DM Created!\nEvent ID: ${data.event_id.substring(0, 16)}...`);
        document.getElementById("dm-text").value = "";
        loadDMInbox();
        loadFeed();
      } else {
        alert("Failed to send DM: " + (data.error || "Unknown error"));
      }
    } catch (err) {
      alert("Direct Message request failed: " + err);
    }
  });
}

function setupCopyNpubHandler() {
  const btn = document.getElementById("btn-copy-npub");
  if (!btn) return;
  btn.addEventListener("click", () => {
    const text = document.getElementById("display-npub").innerText;
    navigator.clipboard.writeText(text).then(() => {
      btn.innerText = "COPIED!";
      setTimeout(() => btn.innerText = "COPY NPUB KEY", 2000);
    });
  });
}
