// State
let conversationHistory = [];
let currentTweet = "";

// DOM elements
const els = {
  settingsPanel: document.getElementById("settings-panel"),
  mainPanel: document.getElementById("main-panel"),
  openSettings: document.getElementById("open-settings"),
  closeSettings: document.getElementById("close-settings"),
  saveSettings: document.getElementById("save-settings"),
  apiKey: document.getElementById("api-key"),
  persona: document.getElementById("persona"),
  tweetInput: document.getElementById("tweet-input"),
  direction: document.getElementById("direction"),
  generateBtn: document.getElementById("generate-btn"),
  outputSection: document.getElementById("output-section"),
  replyOutput: document.getElementById("reply-output"),
  charCount: document.getElementById("char-count"),
  copyBtn: document.getElementById("copy-btn"),
  shorterBtn: document.getElementById("shorter-btn"),
  casualBtn: document.getElementById("casual-btn"),
  spicierBtn: document.getElementById("spicier-btn"),
  regenBtn: document.getElementById("regen-btn"),
  iterateInput: document.getElementById("iterate-input"),
  iterateBtn: document.getElementById("iterate-btn"),
  loading: document.getElementById("loading"),
  error: document.getElementById("error"),
};

// Load saved settings — try sync first (survives extension reloads), fall back to local
chrome.storage.sync.get(["apiKey", "persona"], (syncData) => {
  chrome.storage.local.get(["apiKey", "persona"], (localData) => {
    const data = {
      apiKey: syncData.apiKey || localData.apiKey || "",
      persona: syncData.persona || localData.persona || "",
    };

    if (data.apiKey) els.apiKey.value = data.apiKey;
    if (data.persona) els.persona.value = data.persona;

    // If no API key, show settings on first open
    if (!data.apiKey) {
      els.settingsPanel.classList.remove("hidden");
      els.mainPanel.classList.add("hidden");
    }

    // Ensure both stores are in sync
    if (data.apiKey || data.persona) {
      chrome.storage.sync.set(data);
      chrome.storage.local.set(data);
    }
  });
});

// Settings toggle
els.openSettings.addEventListener("click", () => {
  els.settingsPanel.classList.remove("hidden");
  els.mainPanel.classList.add("hidden");
});

els.closeSettings.addEventListener("click", () => {
  els.settingsPanel.classList.add("hidden");
  els.mainPanel.classList.remove("hidden");
});

els.saveSettings.addEventListener("click", () => {
  const key = els.apiKey.value.trim();
  const persona = els.persona.value.trim();

  if (!key) {
    showError("API key is required");
    return;
  }

  // Save to both sync and local for redundancy
  const settings = { apiKey: key, persona: persona };
  chrome.storage.sync.set(settings);
  chrome.storage.local.set(settings, () => {
    els.settingsPanel.classList.add("hidden");
    els.mainPanel.classList.remove("hidden");
  });
});

// Generate reply
els.generateBtn.addEventListener("click", () => {
  const tweet = els.tweetInput.value.trim();
  if (!tweet) {
    showError("Paste a tweet first");
    return;
  }
  currentTweet = tweet;
  conversationHistory = [];
  generateReply(tweet, els.direction.value.trim());
});

// Quick iteration buttons
els.shorterBtn.addEventListener("click", () => iterate("Make it shorter and punchier. Stay under 280 characters."));
els.casualBtn.addEventListener("click", () => iterate("Make it more casual and conversational."));
els.spicierBtn.addEventListener("click", () => iterate("Make it spicier and more provocative, but still thoughtful."));
els.regenBtn.addEventListener("click", () => {
  conversationHistory = [];
  generateReply(currentTweet, els.direction.value.trim());
});

// Custom iteration
els.iterateBtn.addEventListener("click", () => {
  const instruction = els.iterateInput.value.trim();
  if (!instruction) return;
  iterate(instruction);
  els.iterateInput.value = "";
});

els.iterateInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    els.iterateBtn.click();
  }
});

// Copy
els.copyBtn.addEventListener("click", () => {
  const text = els.replyOutput.innerText;
  navigator.clipboard.writeText(text).then(() => {
    showToast("Copied!");
  });
});

// Char count on edit
els.replyOutput.addEventListener("input", updateCharCount);

function updateCharCount() {
  const len = els.replyOutput.innerText.length;
  els.charCount.textContent = len;
  const countEl = document.querySelector(".char-count");
  countEl.classList.toggle("over", len > 280);
}

// Core: generate reply
async function generateReply(tweet, direction) {
  const apiKey = await getApiKey();
  if (!apiKey) {
    showError("Set your Claude API key in settings first.");
    return;
  }
  const persona = await getPersona();

  showLoading(true);
  hideError();

  const systemPrompt = buildSystemPrompt(persona);
  let userMessage = `Here's the tweet to reply to:\n\n"${tweet}"`;
  if (direction) {
    userMessage += `\n\nDirection: ${direction}`;
  }

  conversationHistory.push({ role: "user", content: userMessage });

  try {
    const reply = await callClaude(apiKey, systemPrompt, conversationHistory);
    conversationHistory.push({ role: "assistant", content: reply });
    showReply(reply);
  } catch (err) {
    showError(err.message);
  } finally {
    showLoading(false);
  }
}

// Core: iterate on reply
async function iterate(instruction) {
  const apiKey = await getApiKey();
  if (!apiKey) return;
  const persona = await getPersona();

  showLoading(true);
  hideError();

  conversationHistory.push({ role: "user", content: instruction });

  try {
    const reply = await callClaude(apiKey, buildSystemPrompt(persona), conversationHistory);
    conversationHistory.push({ role: "assistant", content: reply });
    showReply(reply);
  } catch (err) {
    showError(err.message);
  } finally {
    showLoading(false);
  }
}

// Claude API call
async function callClaude(apiKey, systemPrompt, messages) {
  console.log("Using API key:", apiKey ? apiKey.slice(0, 12) + "..." : "EMPTY");
  const resp = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
      "anthropic-dangerous-direct-browser-access": "true",
    },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1024,
      system: systemPrompt,
      messages: messages,
    }),
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.error?.message || `API error: ${resp.status}`);
  }

  const data = await resp.json();
  return data.content[0].text;
}

function buildSystemPrompt(persona) {
  let prompt = `You are a sharp, thoughtful X/Twitter reply generator.

Rules:
- Output ONLY the reply text. No preamble, no "Here's a reply:", no sign-off, no options, no questions like "want me to adjust?"
- Write like a real human on Twitter. No corporate speak.
- No emojis unless the user specifically asks for them.
- No hashtags unless asked.
- Keep it concise. Default to under 280 characters when possible.
- Don't start with "This" or use the pattern "this not that."
- No em dashes (—) unless absolutely necessary.
- Be direct, clear, and add genuine value or insight.
- Match the energy of the original tweet.`;

  if (persona) {
    prompt += `\n\nThe user describes their voice/style as: "${persona}"`;
  }

  return prompt;
}

// UI helpers
function showReply(text) {
  els.replyOutput.innerText = text;
  els.outputSection.classList.remove("hidden");
  updateCharCount();
}

function showLoading(show) {
  els.loading.classList.toggle("hidden", !show);
  els.generateBtn.disabled = show;
}

function showError(msg) {
  els.error.textContent = msg;
  els.error.classList.remove("hidden");
}

function hideError() {
  els.error.classList.add("hidden");
}

function showToast(msg) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 1500);
}

function getApiKey() {
  return new Promise((resolve) => {
    chrome.storage.sync.get("apiKey", (syncData) => {
      if (syncData.apiKey) return resolve(syncData.apiKey);
      chrome.storage.local.get("apiKey", (localData) => resolve(localData.apiKey || ""));
    });
  });
}

function getPersona() {
  return new Promise((resolve) => {
    chrome.storage.sync.get("persona", (syncData) => {
      if (syncData.persona) return resolve(syncData.persona);
      chrome.storage.local.get("persona", (localData) => resolve(localData.persona || ""));
    });
  });
}
