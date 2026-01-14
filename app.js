/* ==========================
   RÉFÉRENCES DOM
========================== */
const tempoDiv   = document.getElementById("tempo");
const historyDiv = document.getElementById("history");
const updatedDiv = document.getElementById("updated");

/* ==========================
   OUTILS
========================== */
function dayLabel(dateStr, index) {
  const d = new Date(dateStr);
  const jours = ["Dimanche","Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi"];
  if (index === 0) return "Aujourd’hui";
  if (index === 1) return "Demain";
  return jours[d.getDay()];
}

function verdictLabel(result) {
  if (result === "correct") return "✅ Bonne prédiction";
  if (result === "partial") return "⚠️ Zone correcte";
  if (result === "wrong")   return "❌ Mauvaise prédiction";
  return "⏳ En attente de validation";
}

/* ==========================
   PROBABILITÉS À AFFICHER
   🔑 CORRECTION MAJEURE
========================== */
function getDisplayProbabilities(day) {
  if (day.fixed === true) {
    return {
      rouge: day.couleur === "rouge" ? 100 : 0,
      blanc: day.couleur === "blanc" ? 100 : 0,
      bleu:  day.couleur === "bleu"  ? 100 : 0
    };
  }
  return day.probabilites;
}

/* ==========================
   POINT D’ENTRÉE UNIQUE
========================== */
Promise.all([
  fetch("tempo.json?v=" + Date.now()).then(r => r.json()),
  fetch("history.json?v=" + Date.now()).then(r => r.json()),
  fetch("ML/ml_predictions.json?v=" + Date.now()).then(r => r.json()).catch(() => []),
  fetch("meta.json?v=" + Date.now()).then(r => r.json())
]).then(([tempo, history, mlData, meta]) => {

  if (!tempo || !tempo.length) {
    tempoDiv.innerHTML = "<p>Données Tempo indisponibles</p>";
    return;
  }

  updateMeta(meta);
  renderTempo(tempo, mlData);
  renderHistory(history);
  computeCounters(tempo);

});

/* ==========================
   META
========================== */
function updateMeta(meta) {
  if (!updatedDiv || !meta?.updatedAt) return;
  updatedDiv.textContent =
    "Dernière mise à jour : " +
    new Date(meta.updatedAt).toLocaleString("fr-FR");
}

/* ==========================
   TEMPO + ML
========================== */
function renderTempo(days, mlData) {

  const mlByDate = {};
  mlData.forEach(p => mlByDate[p.date] = p);

  tempoDiv.innerHTML = "";

  days.forEach((day, index) => {

    const p = getDisplayProbabilities(day);

    const confidence = day.fixed
      ? 100
      : Math.max(p.rouge, p.blanc, p.bleu);

    const icons = [];
    if (day.sources?.reel) icons.push("✔️");
    if (day.sources?.meteo) icons.push("☁️");
    if (day.sources?.rte) icons.push("⚡");
    if (day.sources?.historique) icons.push("📊");

    const ml = (!day.fixed && mlByDate[day.date]) ? mlByDate[day.date] : null;

    let mlConfidence = 0;
    if (ml?.mlProbabilities) {
      mlConfidence = Math.max(
        ml.mlProbabilities.rouge || 0,
        ml.mlProbabilities.blanc || 0,
        ml.mlProbabilities.bleu || 0
      );
    }

    const card = document.createElement("div");
    card.className = "day " + day.couleur;

    card.innerHTML = `
      <strong>${dayLabel(day.date, index)}</strong><br>
      <span class="date">${day.date}</span><br><br>

      <b>${day.couleur.toUpperCase()}</b>
      <div class="sources">${icons.join(" ")}</div>

      <br>
      🔴 ${p.rouge}%<br>
      ⚪ ${p.blanc}%<br>
      🔵 ${p.bleu}%

      <div class="confidence-wrapper">
        <div class="confidence-bar">
          <div class="confidence-fill" style="width:${confidence}%"></div>
        </div>
        <div class="confidence-label">Confiance moteur : ${confidence}%</div>
      </div>

      ${ml ? `
        <div class="ml-box ml-${ml.mlPrediction}">
          🧠 <b>ML :</b> ${ml.mlPrediction.toUpperCase()}<br>
          🔴 ${ml.mlProbabilities.rouge ?? 0}%
          ⚪ ${ml.mlProbabilities.blanc ?? 0}%
          🔵 ${ml.mlProbabilities.bleu ?? 0}%

          <div class="ml-bar">
            <div class="ml-fill" style="width:${mlConfidence}%"></div>
          </div>
          <div class="confidence-label">Confiance ML : ${mlConfidence}%</div>
        </div>
      ` : ""}
    `;

    tempoDiv.appendChild(card);
  });
}

/* ==========================
   HISTORIQUE — VALIDÉ EDF
========================== */
function renderHistory(history = []) {

  const today = new Date();
  today.setHours(0,0,0,0);

  const visibles = history
    .filter(h => h.realColor && new Date(h.date) <= today)
    .sort((a,b) => new Date(b.date) - new Date(a.date))
    .slice(0, 10);

  if (visibles.length === 0) {
    historyDiv.innerHTML = "<p>Aucune prédiction validée par EDF</p>";
    return;
  }

  historyDiv.innerHTML = visibles.map(h => `
    <div class="history-card">
      <b>${h.date}</b><br>
      Prédiction J-${h.horizon} :
      <b>${h.predictedColor.toUpperCase()}</b><br>
      Résultat réel :
      <b>${h.realColor.toUpperCase()}</b><br>
      ${verdictLabel(h.result)}
    </div>
  `).join("");
}

/* ==========================
   COMPTEURS TEMPO (EDF)
========================== */
function computeCounters() {

  document.getElementById("count-rouge").textContent = 17;
  document.getElementById("count-blanc").textContent = 24;
  document.getElementById("count-bleu").textContent  = 189;
}
