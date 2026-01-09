const tempoDiv = document.getElementById("tempo");
const statsDiv = document.getElementById("stats");
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
  return jours[d.getDay()].charAt(0).toUpperCase() +
         jours[d.getDay()].slice(1);
}

// Verdict lisible
function verdictLabel(result) {
  if (result === "correct") return "✅ Bonne prédiction";
  if (result === "partial") return "⚠️ Acceptable";
  if (result === "wrong") return "❌ Mauvaise";
  return "";
}

// Classe CSS selon confiance
function confidenceClass(value) {
  if (value >= 66) return "conf-high";
  if (value >= 46) return "conf-medium";
  return "conf-low";
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

        // 🔹 Confiance = probabilité max
        const confidence = Math.max(
          day.probabilites.rouge,
          day.probabilites.blanc,
          day.probabilites.bleu
        );

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
          🔵 ${day.probabilites.bleu}%<br>

          <!-- BARRE DE CONFIANCE -->
          <div class="confidence">
            <div class="confidence-label">
              Confiance : <b>${confidence}%</b>
            </div>
            <div class="confidence-bar">
              <div class="confidence-fill ${confidenceClass(confidence)}"
                   style="width:${confidence}%"></div>
            </div>
          </div>
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
   FIABILITÉ – VERSION SIMPLE
========================== */
if (statsDiv) {
  fetch("stats.json?v=" + Date.now())
    .then(res => res.json())
    .then(stats => {
      const total = stats.total || 0;

      statsDiv.innerHTML = `
        <p><b>État actuel :</b></p>
        <ul>
          <li>L’application apprend progressivement</li>
          <li>${total} jour${total > 1 ? "s" : ""} analysé${total > 1 ? "s" : ""}</li>
        </ul>

        <p><b>Résultats observés :</b></p>
        <ul>
          <li>✅ Bonne prédiction : ${stats.correct}</li>
          <li>⚠️ Acceptable : ${stats.partial}</li>
          <li>❌ Mauvaise : ${stats.wrong}</li>
        </ul>

        <details>
          <summary>Voir les détails techniques</summary>
          <p>Exactement correct : ${stats.accuracy}%</p>
          <p>Zone correcte : ${stats.accuracyWithPartial}%</p>
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
========================== */
if (historyDiv) {
  fetch("history.json?v=" + Date.now())
    .then(res => res.json())
    .then(history => {
      const resolved = history.filter(h => h.realColor);

      if (resolved.length === 0) {
        historyDiv.innerHTML =
          "<p>Aucune prédiction passée évaluée pour le moment</p>";
        return;
      }

      historyDiv.innerHTML = resolved
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
    })
    .catch(() => {
      historyDiv.innerHTML =
        "<p>Impossible de charger l’historique</p>";
    });
}
