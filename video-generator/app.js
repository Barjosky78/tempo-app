import { fal } from "https://esm.sh/@fal-ai/client@1";

const MAX_IMAGES = 9;
const STORAGE_KEY = "seedance_fal_api_key";
const HISTORY_KEY = "seedance_history";
const MAX_HISTORY = 10;
const LEDGER_KEY = "seedance_spend_ledger";
const MAX_LEDGER = 2000;

// Prix par seconde en USD. 720p confirmés sur les pages de prix fal.ai ;
// 480p estimés (non confirmés officiellement) — à vérifier sur fal.ai/pricing.
const PRICING = {
  standard: { "480p": 0.14, "720p": 0.3034 },
  fast: { "480p": 0.11, "720p": 0.2419 },
};
const DEFAULT_DURATION_RANGE = [4, 15];

const el = (id) => document.getElementById(id);

const apiKeyInput = el("apiKey");
const rememberKeyInput = el("rememberKey");
const toggleKeyVisibility = el("toggleKeyVisibility");
const dropzone = el("dropzone");
const fileInput = el("fileInput");
const thumbsEl = el("thumbs");
const promptInput = el("prompt");
const tierInput = el("tier");
const resolutionInput = el("resolution");
const durationInput = el("duration");
const aspectRatioInput = el("aspectRatio");
const bitrateModeInput = el("bitrateMode");
const seedInput = el("seed");
const generateAudioInput = el("generateAudio");
const generateBtn = el("generateBtn");
const statusEl = el("status");
const resultCard = el("resultCard");
const resultVideo = el("resultVideo");
const downloadBtn = el("downloadBtn");
const openBtn = el("openBtn");
const historyEl = el("history");
const costEstimateEl = el("costEstimate");
const spendSummaryEl = el("spendSummary");
const spendMonthsEl = el("spendMonths");

/** @type {{file: File, url: string}[]} */
let images = [];

// ---------- API key persistence ----------

const savedKey = localStorage.getItem(STORAGE_KEY);
if (savedKey) {
  apiKeyInput.value = savedKey;
} else {
  rememberKeyInput.checked = false;
}

apiKeyInput.addEventListener("input", () => {
  if (rememberKeyInput.checked) {
    localStorage.setItem(STORAGE_KEY, apiKeyInput.value.trim());
  }
});

rememberKeyInput.addEventListener("change", () => {
  if (rememberKeyInput.checked) {
    localStorage.setItem(STORAGE_KEY, apiKeyInput.value.trim());
  } else {
    localStorage.removeItem(STORAGE_KEY);
  }
});

toggleKeyVisibility.addEventListener("click", () => {
  apiKeyInput.type = apiKeyInput.type === "password" ? "text" : "password";
});

// ---------- Image upload / previews ----------

dropzone.addEventListener("click", () => fileInput.click());

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("dragover");
});

dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  addFiles(e.dataTransfer.files);
});

fileInput.addEventListener("change", () => {
  addFiles(fileInput.files);
  fileInput.value = "";
});

function addFiles(fileList) {
  const accepted = ["image/png", "image/jpeg", "image/webp"];
  for (const file of fileList) {
    if (images.length >= MAX_IMAGES) {
      setStatus(`Maximum ${MAX_IMAGES} photos.`, "error");
      break;
    }
    if (!accepted.includes(file.type)) continue;
    images.push({ file, url: URL.createObjectURL(file) });
  }
  renderThumbs();
  renderCostEstimate();
}

function renderThumbs() {
  thumbsEl.innerHTML = "";
  images.forEach((img, i) => {
    const div = document.createElement("div");
    div.className = "thumb";
    div.innerHTML = `
      <img src="${img.url}" alt="photo ${i + 1}">
      <span class="badge">${i + 1}</span>
      <button type="button" class="remove" title="Retirer">✕</button>
    `;
    div.querySelector(".remove").addEventListener("click", () => {
      URL.revokeObjectURL(img.url);
      images.splice(i, 1);
      renderThumbs();
      renderCostEstimate();
    });
    thumbsEl.appendChild(div);
  });
}

// ---------- Status helper ----------

function setStatus(message, kind = "") {
  statusEl.hidden = !message;
  statusEl.textContent = message;
  statusEl.className = "status" + (kind ? ` ${kind}` : "");
}

// ---------- History ----------

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
  } catch {
    return [];
  }
}

function saveHistoryEntry(entry) {
  const history = loadHistory();
  history.unshift(entry);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, MAX_HISTORY)));
  renderHistory();
}

function renderHistory() {
  const history = loadHistory();
  if (history.length === 0) {
    historyEl.innerHTML = `<p class="history-empty">Aucune génération pour l'instant.</p>`;
    return;
  }
  historyEl.innerHTML = "";
  history.forEach((entry) => {
    const div = document.createElement("div");
    div.className = "history-item";
    const date = new Date(entry.date).toLocaleString("fr-FR");
    const costLabel = typeof entry.costUSD === "number" ? ` · ${formatUSD(entry.costUSD)}` : "";
    div.innerHTML = `
      <div>${escapeHtml(entry.prompt || "(sans prompt)")}</div>
      <video src="${entry.url}" controls preload="metadata" muted></video>
      <div class="meta"><span>${date}</span><span>${entry.resolution} · ${entry.duration}s · ${entry.tier}${costLabel}</span></div>
    `;
    historyEl.appendChild(div);
  });
}

function escapeHtml(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}

// ---------- Cost estimation ----------

function formatUSD(n) {
  return `$${n.toFixed(2)}`;
}

function rateFor(tier, resolution) {
  return PRICING[tier]?.[resolution] ?? PRICING.standard["720p"];
}

function estimateCost(tier, resolution, durationValue) {
  const rate = rateFor(tier, resolution);
  if (durationValue === "auto") {
    const [min, max] = DEFAULT_DURATION_RANGE;
    return { min: rate * min, max: rate * max, isRange: true };
  }
  const seconds = Number(durationValue) || DEFAULT_DURATION_RANGE[0];
  const cost = rate * seconds;
  return { min: cost, max: cost, isRange: false };
}

function renderCostEstimate() {
  const tier = tierInput.value;
  const resolution = resolutionInput.value;
  const duration = durationInput.value;
  const nImages = images.length;
  const mode = nImages === 0 ? "texte → vidéo" : nImages === 1 ? "image → vidéo" : "référence multi-images";
  const { min, max, isRange } = estimateCost(tier, resolution, duration);
  const amount = isRange
    ? `${formatUSD(min)} – ${formatUSD(max)}`
    : formatUSD(min);
  costEstimateEl.innerHTML = `💰 Coût estimé pour cette génération (${mode}) : <span class="amount">${amount}</span>${resolution === "480p" ? " (480p : estimation approximative)" : ""}`;
}

[tierInput, resolutionInput, durationInput].forEach((input) =>
  input.addEventListener("change", renderCostEstimate)
);

// ---------- Spend ledger (monthly tracking) ----------

function loadLedger() {
  try {
    return JSON.parse(localStorage.getItem(LEDGER_KEY)) || [];
  } catch {
    return [];
  }
}

function addSpend(costUSD, date = Date.now()) {
  const ledger = loadLedger();
  ledger.push({ date, costUSD });
  localStorage.setItem(LEDGER_KEY, JSON.stringify(ledger.slice(-MAX_LEDGER)));
  renderSpend();
}

function monthKey(timestamp) {
  const d = new Date(timestamp);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function monthLabel(key) {
  const [y, m] = key.split("-");
  const d = new Date(Number(y), Number(m) - 1, 1);
  return d.toLocaleDateString("fr-FR", { month: "short", year: "numeric" });
}

function renderSpend() {
  const ledger = loadLedger();
  const now = new Date();
  const currentKey = monthKey(now.getTime());

  const totals = new Map();
  for (const entry of ledger) {
    const key = monthKey(entry.date);
    totals.set(key, (totals.get(key) || 0) + entry.costUSD);
  }

  const currentMonthTotal = totals.get(currentKey) || 0;
  const currentMonthCount = ledger.filter((e) => monthKey(e.date) === currentKey).length;
  const allTimeTotal = ledger.reduce((sum, e) => sum + e.costUSD, 0);

  spendSummaryEl.innerHTML = `
    <div class="spend-tile">
      <div class="label">Ce mois-ci</div>
      <div class="value">${formatUSD(currentMonthTotal)}</div>
    </div>
    <div class="spend-tile">
      <div class="label">Vidéos ce mois-ci</div>
      <div class="value">${currentMonthCount}</div>
    </div>
    <div class="spend-tile">
      <div class="label">Total (historique local)</div>
      <div class="value">${formatUSD(allTimeTotal)}</div>
    </div>
  `;

  const sortedKeys = Array.from(totals.keys()).sort().reverse().slice(0, 6);
  const maxTotal = Math.max(...sortedKeys.map((k) => totals.get(k)), 0.01);

  spendMonthsEl.innerHTML = sortedKeys.length
    ? sortedKeys
        .map((key) => {
          const total = totals.get(key);
          const pct = Math.max(4, Math.round((total / maxTotal) * 100));
          return `
            <div class="spend-month-row">
              <span>${monthLabel(key)}</span>
              <span class="spend-bar-track"><span class="spend-bar-fill" style="width:${pct}%"></span></span>
              <span>${formatUSD(total)}</span>
            </div>
          `;
        })
        .join("")
    : `<p class="history-empty">Aucune dépense enregistrée pour l'instant.</p>`;
}

renderHistory();
renderCostEstimate();
renderSpend();

// ---------- Download ----------

async function downloadFile(url, filename) {
  const response = await fetch(url);
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = objectUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(objectUrl);
}

// ---------- Generation ----------

generateBtn.addEventListener("click", generate);

async function generate() {
  const apiKey = apiKeyInput.value.trim();
  const prompt = promptInput.value.trim();

  if (!apiKey) {
    setStatus("Renseigne ta clé API fal.ai.", "error");
    return;
  }
  if (!prompt) {
    setStatus("Écris un prompt décrivant la vidéo souhaitée.", "error");
    return;
  }

  fal.config({ credentials: apiKey });

  generateBtn.disabled = true;
  resultCard.hidden = true;

  try {
    let imageUrls = [];
    if (images.length > 0) {
      setStatus(`Envoi des photos (0/${images.length})…`);
      for (let i = 0; i < images.length; i++) {
        const url = await fal.storage.upload(images[i].file);
        imageUrls.push(url);
        setStatus(`Envoi des photos (${i + 1}/${images.length})…`);
      }
    }

    const tier = tierInput.value;
    const resolution = resolutionInput.value;
    const duration = durationInput.value;
    const aspectRatio = aspectRatioInput.value;
    const bitrateMode = bitrateModeInput.value;
    const generateAudio = generateAudioInput.checked;
    const seed = seedInput.value ? Number(seedInput.value) : undefined;

    let mode;
    const input = {
      prompt,
      resolution,
      duration,
      aspect_ratio: aspectRatio,
      generate_audio: generateAudio,
      bitrate_mode: bitrateMode,
    };
    if (seed !== undefined && !Number.isNaN(seed)) {
      input.seed = seed;
    }

    if (imageUrls.length === 0) {
      mode = "text-to-video";
    } else if (imageUrls.length === 1) {
      mode = "image-to-video";
      input.image_url = imageUrls[0];
    } else {
      mode = "reference-to-video";
      input.image_urls = imageUrls;
    }

    const endpointId = `bytedance/seedance-2.0/${tier === "fast" ? "fast/" : ""}${mode}`;

    setStatus(`Génération en cours (${endpointId})…\nCela peut prendre de 1 à quelques minutes.`);

    const result = await fal.subscribe(endpointId, {
      input,
      logs: true,
      onQueueUpdate: (update) => {
        if (update.status === "IN_QUEUE") {
          setStatus(`En file d'attente… position ${update.queue_position ?? "?"}`);
        } else if (update.status === "IN_PROGRESS") {
          const lastLog = update.logs?.[update.logs.length - 1]?.message;
          setStatus(`Génération en cours…${lastLog ? `\n${lastLog}` : ""}`);
        }
      },
    });

    const videoUrl = result?.data?.video?.url;
    if (!videoUrl) {
      throw new Error("Réponse inattendue : aucune vidéo trouvée dans le résultat.");
    }

    setStatus("Vidéo générée avec succès !", "success");

    resultVideo.src = videoUrl;
    openBtn.href = videoUrl;
    resultCard.hidden = false;

    downloadBtn.onclick = () => downloadFile(videoUrl, `seedance-${Date.now()}.mp4`);

    const rate = rateFor(tier, resolution);
    const fallbackSeconds = duration === "auto" ? DEFAULT_DURATION_RANGE[0] : Number(duration);
    let spendRecorded = false;
    const recordSpend = (actualSeconds) => {
      if (spendRecorded) return;
      spendRecorded = true;
      const seconds = Number.isFinite(actualSeconds) && actualSeconds > 0 ? actualSeconds : fallbackSeconds;
      const costUSD = rate * seconds;
      addSpend(costUSD);
      saveHistoryEntry({
        prompt,
        url: videoUrl,
        date: Date.now(),
        resolution,
        duration,
        tier,
        costUSD,
      });
    };

    resultVideo.addEventListener(
      "loadedmetadata",
      () => recordSpend(resultVideo.duration),
      { once: true }
    );
    // Filet de sécurité si la métadonnée vidéo ne se charge pas (ex : CORS sur le CDN).
    setTimeout(() => {
      if (!resultVideo.duration || Number.isNaN(resultVideo.duration)) {
        recordSpend(fallbackSeconds);
      }
    }, 4000);
  } catch (err) {
    console.error(err);
    const message = err?.body?.detail
      ? typeof err.body.detail === "string"
        ? err.body.detail
        : JSON.stringify(err.body.detail)
      : err?.message || "Une erreur est survenue.";
    setStatus(`Erreur : ${message}`, "error");
  } finally {
    generateBtn.disabled = false;
  }
}
