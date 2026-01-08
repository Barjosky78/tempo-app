const tempoDiv = document.getElementById("tempo");
const statsDiv = document.getElementById("stats");
const historyDiv = document.getElementById("history");

/* ==========================
   OUTILS
========================== */
function verdictLabel(result) {
  if (result === "correct") return "✅ Bonne prédiction";
  if (result === "partial") return "⚠️ Acceptable";
  if (result === "wrong") return "❌ Mauvaise";
  return "";
}

function horizonStats(history) {
  const map = {};
  history.forEach(h => {
    if (!h.realColor) return;
    if (!map[h.horizon]) map[h.horizon] = { total: 0, correct: 0, partial: 0 };
    map[h.horizon].total++;
    if (h.result === "correct") map[h.horizon].correct++;
    if (h.result === "partial") map[h.horizon].partial++;
  });
  return map;
}

/* ==========================
   TEMPO (existant)
========================== */
fetch("tempo.json")
  .then(res => res.json())
  .then(days => {
    tempoDiv.innerHTML = "";
    days.forEach((day, index) => {
      const card = document.createElement("div");
      card.className = "day " + day.couleur;

      card.innerHTML = `
        <strong>${index === 0 ? "Aujourd’hui" : index === 1 ? "Demain" : "J+" + index}</strong><br>
        ${day.date}<br>
        <b>${day.couleur.toUpperCase()}</b><br>
        🔴 ${day.probabilites.rouge}% |
        ⚪ ${day.probabilites.blanc}% |
        🔵 ${day.probabilites.bleu}%
      `;
      tempoDiv.appendChild(card);
    });
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
  });

/* ==========================
   HISTORIQUE + HORIZONS
========================== */
fetch("history.json")
  .then(res => res.json())
  .then(history => {
    const resolved = history.filter(h => h.realColor);

    // 🕒 Historique récent
    historyDiv.innerHTML = resolved
      .slice(-10)
      .reverse()
      .map(h => `
        <div class="history-card">
          <b>${h.date}</b> (prévu J-${h.horizon})<br>
          Prédit : <b>${h.predictedColor}</b><br>
          Réel : <b>${h.realColor}</b><br>
          ${verdictLabel(h.result)}
        </div>
      `)
      .join("");

    // 📊 Stats par horizon
    const byHorizon = horizonStats(history);
    const horizonHtml = Object.keys(byHorizon)
      .sort((a,b)=>a-b)
      .map(h => {
        const d = byHorizon[h];
        const acc = Math.round(d.correct / d.total * 100);
        const acc2 = Math.round((d.correct + d.partial) / d.total * 100);
        return `
          <div>
            J-${h} → ${acc}% (strict) / ${acc2}% (élargi)
          </div>
        `;
      })
      .join("");

    statsDiv.innerHTML += `<h3>📈 Précision par horizon</h3>${horizonHtml}`;
  });
