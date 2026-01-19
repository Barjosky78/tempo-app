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
  const jours = ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"];
  if (index === 0) return "Aujourd'hui";
  if (index === 1) return "Demain";
  return jours[d.getDay()];
}

function verdictLabel(result) {
  if (result === "correct") return "✅ Bonne prédiction";
  if (result === "partial") return "⚠️ Zone correcte";
  if (result === "wrong")   return "❌ Mauvaise prédiction";
  return "⏳ En attente de validation";
}

function formatDate(dateStr) {
  const d = new Date(dateStr);
  return d.toLocaleDateString("fr-FR", { 
    weekday: 'short', 
    day: 'numeric', 
    month: 'short' 
  });
}

/* ==========================
   PROBABILITÉS À AFFICHER
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
   ICÔNES SOURCES
========================== */
function getSourceIcons(sources) {
  const icons = [];
  if (sources?.reel) icons.push('<span title="Couleur officielle EDF">✔️</span>');
  if (sources?.regle_edf) icons.push('<span title="Règle EDF (dimanche/samedi)">📋</span>');
  if (sources?.meteo) icons.push('<span title="Basé sur la météo">☁️</span>');
  if (sources?.rte) icons.push('<span title="Consommation RTE">⚡</span>');
  if (sources?.historique) icons.push('<span title="Historique Tempo">📊</span>');
  if (sources?.hellowatt) icons.push('<span title="Source HelloWatt">🌐</span>');
  return icons.join(" ");
}

/* ==========================
   POINT D'ENTRÉE UNIQUE
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
  computeCounters(meta);

}).catch(err => {
  console.error("Erreur chargement données:", err);
  tempoDiv.innerHTML = "<p>Erreur de chargement des données</p>";
});

/* ==========================
   META + MISE À JOUR
========================== */
function updateMeta(meta) {
  if (!updatedDiv || !meta?.updatedAt) return;
  
  const updateDate = new Date(meta.updatedAt);
  const now = new Date();
  const diffMinutes = Math.floor((now - updateDate) / 60000);
  
  let relativeTime = "";
  if (diffMinutes < 1) relativeTime = "à l'instant";
  else if (diffMinutes < 60) relativeTime = `il y a ${diffMinutes} min`;
  else if (diffMinutes < 1440) relativeTime = `il y a ${Math.floor(diffMinutes/60)}h`;
  else relativeTime = `il y a ${Math.floor(diffMinutes/1440)}j`;
  
  updatedDiv.innerHTML = `
    Dernière mise à jour : ${updateDate.toLocaleString("fr-FR")} 
    <span class="relative-time">(${relativeTime})</span>
  `;
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

    const icons = getSourceIcons(day.sources);

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
    card.className = `day ${day.couleur}${day.fixed ? ' official' : ''}`;

    // Badge pour J0 officiel
    const officialBadge = day.fixed && index === 0 
      ? '<span class="badge-official">OFFICIEL</span>' 
      : '';
    
    // Badge pour prédiction
    const predictionBadge = !day.fixed && index > 0 
      ? `<span class="badge-prediction">J+${index}</span>` 
      : '';

    card.innerHTML = `
      <div class="day-header">
        <strong>${dayLabel(day.date, index)}</strong>
        ${officialBadge}${predictionBadge}
      </div>
      <span class="date">${formatDate(day.date)}</span>

      <div class="color-display">
        <b class="color-${day.couleur}">${day.couleur.toUpperCase()}</b>
      </div>
      
      <div class="sources">${icons}</div>

      <div class="probabilities">
        <div class="prob-row">
          <span class="prob-color">🔴</span>
          <div class="prob-bar-container">
            <div class="prob-bar rouge" style="width:${p.rouge}%"></div>
          </div>
          <span class="prob-value">${p.rouge}%</span>
        </div>
        <div class="prob-row">
          <span class="prob-color">⚪</span>
          <div class="prob-bar-container">
            <div class="prob-bar blanc" style="width:${p.blanc}%"></div>
          </div>
          <span class="prob-value">${p.blanc}%</span>
        </div>
        <div class="prob-row">
          <span class="prob-color">🔵</span>
          <div class="prob-bar-container">
            <div class="prob-bar bleu" style="width:${p.bleu}%"></div>
          </div>
          <span class="prob-value">${p.bleu}%</span>
        </div>
      </div>

      <div class="confidence-wrapper">
        <div class="confidence-bar">
          <div class="confidence-fill ${day.couleur}" style="width:${confidence}%"></div>
        </div>
        <div class="confidence-label">Confiance : ${confidence}%</div>
      </div>

      ${ml ? `
        <div class="ml-box ml-${ml.mlPrediction}">
          <div class="ml-header">🧠 Prédiction ML</div>
          <b>${ml.mlPrediction.toUpperCase()}</b>
          <div class="ml-probs">
            🔴 ${ml.mlProbabilities.rouge ?? 0}%
            ⚪ ${ml.mlProbabilities.blanc ?? 0}%
            🔵 ${ml.mlProbabilities.bleu ?? 0}%
          </div>
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
  today.setHours(0, 0, 0, 0);

  const visibles = history
    .filter(h => h.realColor && new Date(h.date) <= today)
    .sort((a, b) => new Date(b.date) - new Date(a.date))
    .slice(0, 10);

  if (visibles.length === 0) {
    historyDiv.innerHTML = "<p class='no-history'>Aucune prédiction validée par EDF pour le moment</p>";
    return;
  }

  historyDiv.innerHTML = visibles.map(h => `
    <div class="history-card ${h.result}">
      <div class="history-date">${formatDate(h.date)}</div>
      <div class="history-prediction">
        Prédiction J-${h.horizon} : 
        <span class="color-${h.predictedColor}">${h.predictedColor.toUpperCase()}</span>
      </div>
      <div class="history-real">
        Résultat réel : 
        <span class="color-${h.realColor}">${h.realColor.toUpperCase()}</span>
      </div>
      <div class="history-verdict">${verdictLabel(h.result)}</div>
    </div>
  `).join("");
}

/* ==========================
   COMPTEURS TEMPO (DYNAMIQUES)
========================== */
function computeCounters(meta) {
  const countRouge = document.getElementById("count-rouge");
  const countBlanc = document.getElementById("count-blanc");
  const countBleu = document.getElementById("count-bleu");

  // Utiliser les données de meta.json si disponibles
  if (meta?.remaining) {
    if (countRouge) countRouge.textContent = meta.remaining.rouge;
    if (countBlanc) countBlanc.textContent = meta.remaining.blanc;
    if (countBleu) countBleu.textContent = meta.remaining.bleu;
  } else {
    // Valeurs par défaut (milieu de saison approximatif)
    // Saison complète : 300 bleu, 43 blanc, 22 rouge
    // On estime en fonction de la date
    const today = new Date();
    const seasonStart = new Date(today.getFullYear(), 8, 1); // 1er septembre
    if (today < seasonStart) {
      seasonStart.setFullYear(seasonStart.getFullYear() - 1);
    }
    
    const daysSinceStart = Math.floor((today - seasonStart) / (1000 * 60 * 60 * 24));
    const seasonProgress = Math.min(1, daysSinceStart / 243); // ~243 jours de saison
    
    const usedRouge = Math.round(22 * seasonProgress);
    const usedBlanc = Math.round(43 * seasonProgress);
    const usedBleu = Math.round(300 * seasonProgress);
    
    if (countRouge) countRouge.textContent = Math.max(0, 22 - usedRouge);
    if (countBlanc) countBlanc.textContent = Math.max(0, 43 - usedBlanc);
    if (countBleu) countBleu.textContent = Math.max(0, 300 - usedBleu);
  }
}

/* ==========================
   SERVICE WORKER (PWA)
========================== */
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('service-worker.js')
    .then(() => console.log('Service Worker enregistré'))
    .catch(err => console.log('Service Worker erreur:', err));
}
