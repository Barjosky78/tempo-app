const tempoDiv = document.getElementById("tempo");
const statsDiv = document.getElementById("stats");
const historyDiv = document.getElementById("history");
const updatedDiv = document.getElementById("updated"); // ⏱️ AJOUT

/* ==========================
   OUTILS
========================== */

// Nom du jour en français
function dayLabel(dateStr, index) {
  const d = new Date(dateStr);
  const jours = ["dimanche","lundi","mardi","mercredi","jeudi","vendredi","samedi"];
  const name = jours[d.getDay()];

  if (index === 0) return "Aujourd’hui";
  if (index === 1) return "Demain";
  return name.charAt(0).toUpperCase() + name.slice(1);
}

// Verdict lisible
function verdictLabel(result) {
  if (result === "correct") return "✅ Bonne prédiction";
  if (result === "partial") return "⚠️ Acceptable";
  if (result === "wrong") return "❌ Mauvaise";
  return "";
}

/* ==========================
   ⏱️ HEURE DE MISE À JOUR
========================== */

fetch("meta.json")
  .then(res => res.json())
  .then(meta => {
    if (!updatedDiv) return;
    const d = new Date(meta.updatedAt);
    updatedDiv.textContent =
      "Dernière mise à jour : " + d.toLocaleString("fr-FR");
  })
  .catch(() => {
    if (updatedDiv) {
      updatedDiv.textContent = "Dernière mise à jour inconnue";
    }
  });

/* ==========================
   PRÉVISIONS TEMPO
========================== */
fetch("tempo.json")
  .then(res => res.json())
  .then(days => {
    tempoDiv.innerHTML = "";

    days.forEach((day, index) => {
      const card = document.createElement("div");
      card.className = "day " + day.couleur;

      card.innerHTML = `
        <strong>${dayLabel(day.date, index)}</strong><br>
        <span class="date">${day.date}</span><br><br>

        <b>${day.couleur.toUpperCase()}</b><br><br>

        🔴 ${day.probabilites.rouge}%<br>
        ⚪ ${day.probabilites.blanc}%<br>
        🔵 ${day.probabilites.bleu}%
      `;

      tempoDiv.appendChild(card);
    });
  })
  .catch(() => {
    tempoDiv.innerHTML = "<p>Erreur de chargement des prévisions</p>";
  });

/* ==========================
   FIABILITÉ – VERSION SIMPLE
========================== */
fetch("stats.json")
  .then(res => res.json())
  .then(stats => {
    const total = stats.total || 0;

    let intro = `
      <p><b>État actuel :</b></p>
      <ul>
        <li>L’application apprend progressivement</li>
        <li>${total} jour${total > 1 ? "s" : ""} analysé${total > 1 ? "s" : ""}</li>
      </ul>
    `;

    let resume = `
      <p><b>Résultats observés :</b></p>
      <ul>
        <li>✅ Bonne prédiction : ${stats.correct} jour${stats.correct > 1 ? "s" : ""}</li>
        <li>⚠️ Acceptable : ${stats.partial} jour${stats.partial > 1 ? "s" : ""}</li>
        <li>❌ Mauvaise : ${stats.wrong} jour${stats.wrong > 1 ? "s" : ""}</li>
      </ul>
    `;

    let details = `
      <details>
        <summary>Voir les détails techniques</summary>
        <p>Exactement correct : ${stats.accuracy}%</p>
        <p>Zone correcte : ${stats.accuracyWithPartial}%</p>
      </details>
    `;

    statsDiv.innerHTML = intro + resume + details;
  })
  .catch(() => {
    statsDiv.innerHTML = "<p>Aucune donnée de fiabilité disponible</p>";
  });

/* ==========================
   HISTORIQUE DES PRÉDICTIONS
========================== */
fetch("history.json")
  .then(res => res.json())
  .then(history => {
    const resolved = history.filter(h => h.realColor);

    if (resolved.length === 0) {
      historyDiv.innerHTML = "<p>Aucune prédiction passée évaluée pour le moment</p>";
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
    historyDiv.innerHTML = "<p>Impossible de charger l’historique</p>";
  });
