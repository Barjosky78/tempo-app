/* =========================================================
   TEMPO EDF – APPLICATION PRINCIPALE
   Version stable – Historique visible dès J-1
========================================================= */

const tempoDiv   = document.getElementById("tempo");
const statsDiv   = document.getElementById("stats");
const historyDiv = document.getElementById("history");
const updatedDiv = document.getElementById("updated");

/* ==========================
   OUTILS
========================== */

// Nom du jour en français
function dayLabel(dateStr, index) {
  const d = new Date(dateStr);
  const jours = [
    "dimanche","lundi","mardi",
    "mercredi","jeudi","vendredi","samedi"
  ];

  if (index === 0) return "Aujourd’hui";
  if (index === 1) return "Demain";

  const name = jours[d.getDay()];
  return name.charAt(0).toUpperCase() + name.slice(1);
}

// Verdict lisible
function verdictLabel(result) {
  if (result === "correct") return "✅ Bonne prédiction";
  if (result === "partial") return "⚠️ Zone correcte";
  if (result === "wrong")   return "❌ Mauvaise prédiction";
  return "⏳ En attente de validation EDF";
}

/* ==========================
   ⏱️ HEURE DE MISE À JOUR
========================== */
if (updatedDiv) {
  fetch("meta.json?v=" + Date.now())
    .then(res => res.json())
    .then(meta => {
      const d = new Date(meta.updatedAt);
      updatedDiv.textContent =
        "Dernière mise à jour : " + d.toLocaleString("fr-FR");
    })
    .catch(() => {
      updatedDiv.textContent = "Dernière mise à jour inconnue";
    });
}

/* ==========================
   PRÉVISIONS TEMPO
========================== */
if (tempoDiv) {
  fetch("tempo.json?v=" + Date.now())
    .then(res => res.json())
    .then(days => {
      tempoDiv.innerHTML = "";

      days.forEach((day, index) => {
        const card = document.createElement("div");
        card.className = "day " + day.couleur;

        const confidence = Math.max(
          day.probabilites.rouge,
          day.probabilites.blanc,
          day.probabilites.bleu
        );

        card.innerHTML = `
          <strong>${dayLabel(day.date, index)}</strong><br>
          <span class="date">${day.date}</span><br><br>

          <b>${day.couleur.toUpperCase()}</b>
          ${day.estimated ? "<div class='tag'>Estimation météo</div>" : ""}
          <br><br>

          🔴 ${day.probabilites.rouge}%<br>
          ⚪ ${day.probabilites.blanc}%<br>
          🔵 ${day.probabilites.bleu}%<br><br>

          <div class="confidence-bar">
            <div class="confidence-fill" style="width:${confidence}%"></div>
          </div>
          <div class="confidence-label">Confiance : ${confidence}%</div>
        `;

        tempoDiv.appendChild(card);
      });
    })
    .catch(() => {
      tempoDiv.innerHTML =
        "<p>Erreur de chargement des prévisions</p>";
    });
}

/* ==========================
   FIABILITÉ / STATS
========================== */
if (statsDiv) {
  fetch("stats.json?v=" + Date.now())
    .then(res => res.json())
    .then(stats => {
      const total = stats.total || 0;

      statsDiv.innerHTML = `
        <p><b>État du modèle :</b></p>
        <ul>
          <li>${total} jour${total > 1 ? "s" : ""} analysé${total > 1 ? "s" : ""}</li>
          <li>Le modèle apprend progressivement</li>
        </ul>

        <p><b>Résultats :</b></p>
        <ul>
          <li>✅ Bonnes prédictions : ${stats.correct}</li>
          <li>⚠️ Zones correctes : ${stats.partial}</li>
          <li>❌ Mauvaises : ${stats.wrong}</li>
        </ul>

        <details>
          <summary>Détails techniques</summary>
          <p>Exactitude stricte : ${stats.accuracy}%</p>
          <p>Exactitude élargie : ${stats.accuracyWithPartial}%</p>
        </details>
      `;
    })
    .catch(() => {
      statsDiv.innerHTML =
        "<p>Aucune donnée de fiabilité disponible</p>";
    });
}

/* ==========================
   HISTORIQUE DES PRÉDICTIONS
   ➜ Visible à partir d’HIER
========================== */
if (historyDiv) {
  fetch("history.json?v=" + Date.now())
    .then(res => res.json())
    .then(history => {

      const today = new Date();
      today.setHours(0,0,0,0);

      // 👉 Afficher tout ce qui est passé (hier inclus)
      const visible = history.filter(h => {
        const d = new Date(h.date);
        d.setHours(0,0,0,0);
        return d < today;
      });

      if (visible.length === 0) {
        historyDiv.innerHTML =
          "<p>Aucune prédiction passée à afficher</p>";
        return;
      }

      historyDiv.innerHTML = visible
        .slice(-15)
        .reverse()
        .map(h => `
          <div class="history-card">
            <b>${h.date}</b><br>
            Prédiction faite J-${h.horizon} : <b>${h.predictedColor}</b><br>
            ${h.realColor ? `Résultat réel : <b>${h.realColor}</b><br>` : ""}
            ${verdictLabel(h.result)}
          </div>
        `)
        .join("");
    })
    .catch(() => {
      historyDiv.innerHTML =
        "<p>Impossible de charger l’historique</p>";
    });
}
