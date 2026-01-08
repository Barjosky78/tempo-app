const tempoDiv = document.getElementById("tempo");

// 🔒 COULEURS OFFICIELLES À FORCER
// 👉 À METTRE À JOUR MANUELLEMENT QUAND RTE CHANGE
const OFFICIEL = {
  today: "blanc",   // <-- AUJOURD'HUI
  tomorrow: "bleu"  // <-- DEMAIN
};

fetch("tempo.json?ts=" + Date.now()) // évite le cache
  .then(res => res.json())
  .then(days => {
    tempoDiv.innerHTML = "";

    if (!Array.isArray(days) || days.length === 0) {
      tempoDiv.innerHTML = "<p>Aucune donnée</p>";
      return;
    }

    // 🔒 FORÇAGE OFFICIEL AUJOURD'HUI / DEMAIN
    if (days[0]) {
      days[0].couleur = OFFICIEL.today;
      days[0].probabilites = { rouge: 0, blanc: 100, bleu: 0 };
    }

    if (days[1]) {
      days[1].couleur = OFFICIEL.tomorrow;
      days[1].probabilites = { rouge: 0, blanc: 0, bleu: 100 };
    }

    // 🧱 AFFICHAGE DES CARTES
    days.forEach((day, index) => {
      const card = document.createElement("div");
      card.className = "day " + day.couleur;

      const label =
        index === 0 ? "Aujourd’hui" :
        index === 1 ? "Demain" :
        "J+" + index;

      card.innerHTML = `
        <div class="date">
          ${label}<br>${day.date}
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
