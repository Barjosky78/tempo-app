const tempoDiv = document.getElementById("tempo");
const historyDiv = document.getElementById("history");
const updatedDiv = document.getElementById("updated");

/* ==========================
   OUTILS
========================== */

function dayLabel(dateStr, index) {
  const d = new Date(dateStr);
  const jours = ["dimanche","lundi","mardi","mercredi","jeudi","vendredi","samedi"];
  if (index === 0) return "Aujourd’hui";
  if (index === 1) return "Demain";
  return jours[d.getDay()].charAt(0).toUpperCase() + jours[d.getDay()].slice(1);
}

function sourceIcons(s) {
  if (!s) return "";
  let icons = "";
  if (s.reel) icons += "⚡ ";
  if (s.meteo) icons += "🌡️ ";
  if (s.rte) icons += "🔌 ";
  if (s.historique) icons += "📊 ";
  return `<div class="sources">${icons}</div>`;
}

function confidenceValue(p) {
  return Math.max(p.rouge, p.blanc, p.bleu);
}

function verdictLabel(result) {
  if (result === "correct") return "✅ Bonne prédiction";
  if (result === "partial") return "⚠️ Acceptable";
  if (result === "wrong") return "❌ Mauvaise";
  return "";
}

/* ==========================
   HEURE DE MISE À JOUR
========================== */
fetch("meta.json?v=" + Date.now())
  .then(res => res.json())
  .then(meta => {
    const d = new Date(meta.updatedAt);
    updatedDiv.textContent =
      "Dernière mise à jour : " + d.toLocaleString("fr-FR");
  });

/* ==========================
   PRÉVISIONS TEMPO
========================== */
fetch("tempo.json?v=" + Date.now())
  .then(res => res.json())
  .then(days => {
    tempoDiv.innerHTML = "";

    days.forEach((day, index) => {
      const conf = confidenceValue(day.probabilites);

      const card = document.createElement("div");
      card.className = "day " + day.couleur;

      card.innerHTML = `
        <strong>${dayLabel(day.date, index)}</strong><br>
        <span class="date">${day.date}</span><br><br>

        <b>${day.couleur.toUpperCase()}</b>
        ${day.estimated ? "<div class='tag'>Estimation météo</div>" : ""}
        <br><br>

        🔴 ${day.probabilites.rouge}%<br>
        ⚪ ${day.probabilites.blanc}%<br>
        🔵 ${day.probabilites.bleu}%<br><br>

        <div class="confidence">
          <div class="confidence-bar" style="width:${conf}%"></div>
        </div>
        <div class="confidence-label">Confiance : ${conf}%</div>

        ${sourceIcons(day.sources)}
      `;

      tempoDiv.appendChild(card);
    });
  });

/* ==========================
   HISTORIQUE (DEPUIS HIER)
========================== */
fetch("history.json?v=" + Date.now())
  .then(res => res.json())
  .then(history => {
    const today = new Date();
    today.setHours(0,0,0,0);

    const past = history.filter(h => {
      const d = new Date(h.date);
      d.setHours(0,0,0,0);
      return d < today && h.realColor;
    });

    if (past.length === 0) {
      historyDiv.innerHTML =
        "<p>Aucune prédiction passée disponible pour le moment.</p>";
      return;
    }

    historyDiv.innerHTML = past
      .slice(-10)
      .reverse()
      .map(h => `
        <div class="history-card">
          <b>${h.date}</b><br>
          Prédiction faite J-${h.horizon} : <b>${h.predictedColor}</b><br>
          Résultat réel : <b>${h.realColor}</b><br>
          ${verdictLabel(h.result)}
        </div>
      `)
      .join("");
  });
