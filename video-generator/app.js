import { fal } from "https://esm.sh/@fal-ai/client@1";

const MAX_IMAGES = 9;
const STORAGE_KEY = "seedance_fal_api_key";
const HISTORY_KEY = "seedance_history";
const MAX_HISTORY = 10;

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
    div.innerHTML = `
      <div>${escapeHtml(entry.prompt || "(sans prompt)")}</div>
      <video src="${entry.url}" controls preload="metadata" muted></video>
      <div class="meta"><span>${date}</span><span>${entry.resolution} · ${entry.duration}s · ${entry.tier}</span></div>
    `;
    historyEl.appendChild(div);
  });
}

function escapeHtml(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}

renderHistory();

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

    saveHistoryEntry({
      prompt,
      url: videoUrl,
      date: Date.now(),
      resolution,
      duration,
      tier,
    });
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
