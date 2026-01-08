const tempoDiv = document.getElementById("tempo");

// Chargement du JSON (anti-cache)
fetch("tempo.json?ts=" + Date.now())
  .then(res => res.json())
  .then(days => {
    tempoDiv.innerHTML = "";

    if (!Array.isArray(days) || days.length === 0) {
      tempoDiv.innerHTML = "<p>Aucune donnée</p>";
      return;
    }

    // Dates de référence
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);

    days.forEach((day, index) => {
      const card = document.createElement("div");

      const dayDate = new Date(day.date);
      dayDate.setHours(0, 0, 0, 0);

      const dayOfWeek = dayDate.getDay(); // 0 = dimanche, 6 = samedi

      // 🔒 RÈGLES TEMPO WEEK-END (UNIQUEMENT POUR J+2 → J+9)
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

      // Label Aujourd’hui / Demain / J+x
      let label = "J+" + index;
      if (dayDate.getTime() === today.getTime()) label = "Aujourd’hui";
      else if (dayDate.getTime() === tomorrow.getTime()) label = "Demain";

      // Date lisible (lundi, mardi, etc.)
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
