const tempoDiv = document.getElementById("tempo");
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
  if (result === "wrong") return "❌ Mauvaise prédiction";
  return "⏳ En attente de validation";
}

/* ==========================
   META
========================== */
fetch("meta.json?v=" + Date.now())
  .then(r => r.json())
  .then(meta => {
    if (!updatedDiv) return;
    updatedDiv.textContent =
      "Dernière mise à jour : " +
      new Date(meta.updatedAt).toLocaleString("fr-FR");
  });

/* ==========================
   CHARGEMENT ML (PAR DATE)
========================== */
let mlByDate = {};

fetch("ML/ml_predictions.json?v=" + Date.now())
  .then(r => r.json())
  .then(data => {
    data.forEach(p => {
      mlByDate[p.date] = p;
    });
  })
  .catch(() => {
    mlByDate = {};
  });

/* ==========================
   PRÉVISIONS TEMPO + ML
========================== */
fetch("tempo.json?v=" + Date.now())
  .then(r => r.json())
  .then(days => {
    tempoDiv.innerHTML = "";

    days.forEach((day, index) => {
      const confidence = day.fixed
        ? 100
        : Math.max(
            day.probabilites.rouge,
            day.probabilites.blanc,
            day.probabilites.bleu
          );

      const icons = [];
      if (day.sources?.reel) icons.push("✔️");
      if (day.sources?.meteo) icons.push("☁️");
      if (day.sources?.rte) icons.push("⚡");
      if (day.sources?.historique) icons.push("📊");

      const ml = mlByDate[day.date] || null;

      let mlConfidence = 0;
      if (ml && ml.mlProbabilities) {
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
        ${day.estimated ? `<div class="tag">Estimation météo</div>` : ""}
        <div class="sources">${icons.join(" ")}</div>

        <br>
        🔴 ${day.probabilites.rouge}%<br>
        ⚪ ${day.probabilites.blanc}%<br>
        🔵 ${day.probabilites.bleu}%

        <div class="confidence-wrapper">
          <div class="confidence-bar">
            <div class="confidence-fill" style="width:${confidence}%"></div>
          </div>
          <div class="confidence-label">Confiance moteur : ${confidence}%</div>
        </div>

        ${ml ? `
          <div class="ml-box">
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
  });

/* ==========================
   HISTORIQUE — À PARTIR D’HIER
========================== */
fetch("history.json?v=" + Date.now())
  .then(r => r.json())
  .then(history => {
    const today = new Date();
    today.setHours(0,0,0,0);

    const visibles = history
      .filter(h => new Date(h.date) < today)
      .sort((a,b) => new Date(b.date) - new Date(a.date))
      .slice(0, 10);

    if (visibles.length === 0) {
      historyDiv.innerHTML =
        "<p>Aucune prédiction passée disponible</p>";
      return;
    }

    historyDiv.innerHTML = visibles.map(h => `
      <div class="history-card">
        <b>${h.date}</b><br>
        Prédiction J-${h.horizon ?? "?"} : <b>${h.predictedColor}</b><br>
        Résultat réel : <b>${h.realColor ?? "En attente"}</b><br>
        ${verdictLabel(h.result)}
      </div>
    `).join("");
  });
