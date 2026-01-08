const tempoDiv = document.getElementById("tempo");
const statsDiv = document.getElementById("stats");
const historyDiv = document.getElementById("history");

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

// Stats par horizon
function horizonStats(history) {
  const map = {};
  history.forEach(h => {
    if (!h.realColor) return;
    if (!map[h.horizon]) {
      map[h.horizon] = { total: 0, correct: 0, partial: 0 };
    }
    map[h.horizon].total++;
    if (h.result === "correct") map[h.horizon].correct++;
    if (h.result === "partial") map[h.horizon].partial++;
  });
  return map;
}

/* ==========================
   TEMPO (prévisions)
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
  .catch(err => {
    tempoDiv.innerHTML = "<p>Erreur chargement tempo.json</p>";
    console.error(err);
  });

/* ==========================
   STATS GLOBALES
========================== */
fetch("stats.json")
  .then(res => res.json())
  .then(stats => {
    statsDiv.innerHTML = `
      <p>🎯 Précision stricte : <b>${stats.accuracy}%</b></p>
      <p>🎯 Précision élargie (±1) : <b>${stats.accuracyWithPartial}%</b></p>
      <p>📅 Prédictions évaluées : ${stats.total}</p>
    `;
  })
  .catch(() => {
    statsDiv.innerHTML = "<p>Aucune statistique disponible</p>";
  });

/* ==========================
   HISTORIQUE + HORIZONS
========================== */
fetch("history.json")
  .then(res => res.json())
  .then(history => {
    const resolved = history.filter(h => h.realColor);

    /* ---- Historique récent ---- */
    historyDiv.innerHTML = resolved
      .slice(-10)
      .reverse()
      .map(h => `
        <div class="history-card">
          <b>${h.date}</b><br>
          Prédiction J-${h.horizon} : <b>${h.predictedColor}</b><br>
          Résultat réel : <b>${h.realColor}</b><br>
          ${verdictLabel(h.result)}
        </div>
      `)
      .join("");

    /* ---- Stats par horizon ---- */
    const byHorizon = horizonStats(history);

    const horizonHtml = Object.keys(byHorizon)
      .sort((a,b)=>a-b)
      .map(h => {
        const d = byHorizon[h];
        const strict = Math.round(d.correct / d.total * 100);
        const extended = Math.round((d.correct + d.partial) / d.total * 100);
        return `
          <div>
            📈 J-${h} → ${strict}% (strict) / ${extended}% (élargi)
          </div>
        `;
      })
      .join("");

    statsDiv.innerHTML += `
      <h3>📊 Précision par horizon</h3>
      ${horizonHtml}
    `;
  })
  .catch(() => {
    historyDiv.innerHTML = "<p>Aucun historique disponible</p>";
  });
