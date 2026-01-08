const tempoDiv = document.getElementById("tempo");
const lastUpdateDiv = document.getElementById("last-update");

// Chargement JSON avec anti-cache
fetch("tempo.json?ts=" + Date.now())
  .then(res => res.json())
  .then(days => {
    tempoDiv.innerHTML = "";

    if (!Array.isArray(days) || days.length === 0) {
      tempoDiv.innerHTML = "<p>Aucune donnée</p>";
      return;
    }

    // Affichage date + heure de mise à jour (locale)
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

    // Références aujourd'hui / demain
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);

    days.forEach((day, index) => {
      const card = document.createElement("div");

      const dayDate = new Date(day.date);
      dayDate.setHours(0, 0, 0, 0);

      const dayOfWeek = dayDate.getDay(); // 0 = dimanche, 6 = samedi

      // 🔒 Règles Tempo week-end (prévisions uniquement)
      if (index >= 2) {
        if (dayOfWeek === 0) {
          day.couleur = "bleu";
          day.probabilites = { rouge: 0, blanc: 0, bleu: 100 };
        }
        if (dayOfWeek === 6 && day.couleur === "rouge") {
          day.couleur = "blanc";
          day.probabilites = { rouge: 0, blanc: 60, bleu: 40 };
        }
      }

      card.className = "day " + day.couleur;

      // Label logique
      let label = "J+" + index;
      if (dayDate.getTime() === today.getTime()) {
        label = "Aujourd’hui";
        card.classList.add("today");
      } else if (dayDate.getTime() === tomorrow.getTime()) {
        label = "Demain";
        card.classList.add("tomorrow");
      }

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

      tempoDiv.appendChild(card);
    });
  })
  .catch(err => {
    tempoDiv.innerHTML = "<p>Erreur JS</p>";
    console.error(err);
  });
