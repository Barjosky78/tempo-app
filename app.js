const tempoDiv = document.getElementById("tempo");

fetch("tempo.json?ts=" + Date.now())
  .then(res => res.json())
  .then(days => {
    tempoDiv.innerHTML = "";

    if (!Array.isArray(days) || days.length === 0) {
      tempoDiv.innerHTML = "<p>Aucune donnée</p>";
      return;
    }

    const today = new Date();
    today.setHours(0,0,0,0);

    const tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);

    days.forEach((day, index) => {
      const card = document.createElement("div");
      card.className = "day " + day.couleur;

      const dayDate = new Date(day.date);
      dayDate.setHours(0,0,0,0);

      let label = "J+" + index;
      if (dayDate.getTime() === today.getTime()) label = "Aujourd’hui";
      else if (dayDate.getTime() === tomorrow.getTime()) label = "Demain";

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
