const todayDiv = document.getElementById("today");
const tomorrowDiv = document.getElementById("tomorrow");
const forecastDiv = document.getElementById("forecast");
const lastUpdateDiv = document.getElementById("last-update");

// 🔢 Calcul de l'indicateur de confiance
function confidenceScore(index, proba) {
  if (index === 0 || index === 1) return 100;

  const baseMap = {
    2: 80,
    3: 75,
    4: 70,
    5: 65,
    6: 60,
    7: 55,
    8: 50,
    9: 45
  };

  let score = baseMap[index] || 45;
  const maxProba = Math.max(proba.rouge, proba.blanc, proba.bleu);

  if (maxProba >= 70) score += 10;
  else if (maxProba >= 60) score += 5;

  return Math.max(30, Math.min(score, 85));
}

// Chargement des données
fetch("tempo.json?ts=" + Date.now())
  .then(res => res.json())
  .then(days => {

    // 🕒 Date & heure de mise à jour
    const now = new Date();
    lastUpdateDiv.textContent =
      "Dernière mise à jour : " +
      now.toLocaleDateString("fr-FR", {
        weekday: "long",
        day: "numeric",
        month: "long"
      }) +
      " à " +
      now.toLocaleTimeString("fr-FR", {
        hour: "2-digit",
        minute: "2-digit"
      });

    days.forEach((day, index) => {
      const card = document.createElement("div");
      card.className = "day " + day.couleur;

      const date = new Date(day.date);
      const dateText = date.toLocaleDateString("fr-FR", {
        weekday: "long",
        day: "numeric",
        month: "long"
      });

      const label =
        index === 0 ? "Aujourd’hui" :
        index === 1 ? "Demain" :
        "J+" + index;

      const confidence = confidenceScore(index, day.probabilites);

      card.innerHTML = `
        <div class="date">${label}<br>${dateText}</div>
        <strong>${day.couleur.toUpperCase()}</strong>

        <div class="proba">
          🔴 ${day.probabilites.rouge}%<br>
          ⚪ ${day.probabilites.blanc}%<br>
          🔵 ${day.probabilites.bleu}%
        </div>

        <div class="confidence">
          Fiabilité : <strong>${confidence}%</strong>
          <div class="confidence-bar">
            <div class="confidence-fill" style="width:${confidence}%"></div>
          </div>
        </div>
      `;

      if (index === 0) {
        todayDiv.appendChild(card);
      } else if (index === 1) {
        tomorrowDiv.appendChild(card);
      } else {
        forecastDiv.appendChild(card);
      }
    });
  })
  .catch(() => {
    forecastDiv.innerHTML = "<p>Erreur chargement données</p>";
  });
