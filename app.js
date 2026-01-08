const todayDiv = document.getElementById("today");
const tomorrowDiv = document.getElementById("tomorrow");
const forecastDiv = document.getElementById("forecast");
const lastUpdateDiv = document.getElementById("last-update");

// Chargement JSON (anti-cache)
fetch("tempo.json?ts=" + Date.now())
  .then(res => res.json())
  .then(days => {

    if (!Array.isArray(days) || days.length === 0) {
      forecastDiv.innerHTML = "<p>Aucune donnée</p>";
      return;
    }

    // 🕒 Date & heure de mise à jour (locale)
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

    // Référence aujourd’hui (minuit local)
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    days.forEach((day, index) => {
      const card = document.createElement("div");

      const dayDate = new Date(day.date);
      dayDate.setHours(0, 0, 0, 0);
      const dayOfWeek = dayDate.getDay(); // 0 = dimanche, 6 = samedi

      // 🔒 Règles Tempo week-end (prévisions uniquement)
      if (index >= 2) {
        // Dimanche = toujours BLEU
        if (dayOfWeek === 0) {
          day.couleur = "bleu";
          day.probabilites = { rouge: 0, blanc: 0, bleu: 100 };
        }

        // Samedi = jamais ROUGE
        if (dayOfWeek === 6 && day.couleur === "rouge") {
          day.couleur = "blanc";
          day.probabilites = { rouge: 0, blanc: 60, bleu: 40 };
        }
      }

      card.className = "day " + day.couleur;

      // Libellé
      const label =
        index === 0 ? "Aujourd’hui" :
        index === 1 ? "Demain" :
        "J+" + index;

      // Date lisible
      const dateTexte = dayDate.toLocaleDateString("fr-FR", {
        weekday: "long",
        day: "numeric",
        month: "long"
      });

      card.innerHTML = `
        <div class="date">
          ${label}<br>${dateTexte}
        </div>
        <strong>${day.couleur.toUpperCase()}</strong>
        <div class="proba">
          🔴 ${day.probabilites.rouge} %<br>
          ⚪ ${day.probabilites.blanc} %<br>
          🔵 ${day.probabilites.bleu} %
        </div>
      `;

      // Placement des cartes
      if (index === 0) {
        todayDiv.appendChild(card);
      } else if (index === 1) {
        tomorrowDiv.appendChild(card);
      } else {
        forecastDiv.appendChild(card);
      }
    });
  })
  .catch(err => {
    forecastDiv.innerHTML = "<p>Erreur chargement données</p>";
    console.error(err);
  });
