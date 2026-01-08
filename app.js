const tempoDiv = document.getElementById("tempo");

fetch("tempo.json?ts=" + Date.now())
  .then(res => res.json())
  .then(days => {
    tempoDiv.innerHTML = "";

    if (!Array.isArray(days) || days.length === 0) {
      tempoDiv.innerHTML = "<p>Aucune donnée</p>";
      return;
    }

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
