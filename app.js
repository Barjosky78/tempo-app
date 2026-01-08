const tempoDiv = document.getElementById("tempo");

fetch("https://www.api-couleur-tempo.fr/api")
  .then(r => r.json())
  .then(data => {
    tempoDiv.innerHTML = ""; // nettoyage
    // Garde jusqu’à J+9 max
    const days = data.slice(0, 10);
    days.forEach((day, index) => {
      const div = document.createElement("div");
      div.className = "day " + day.couleur.toLowerCase();
      const label =
        index === 0 ? "Aujourd'hui" :
        index === 1 ? "Demain" :
        "J+" + index;
      div.innerHTML = `
        <div class="date">${label}<br>${day.date.slice(8,10)}/${day.date.slice(5,7)}</div>
        <div><strong>${day.couleur.toUpperCase()}</strong></div>
        <div class="proba">
          🔴 ${day.probabilites?.rouge ?? 0} %<br>
          ⚪ ${day.probabilites?.blanc ?? 0} %<br>
          🔵 ${day.probabilites?.bleu ?? 0} %
        </div>
      `;
      tempoDiv.appendChild(div);
    });
  })
  .catch(err => {
    tempoDiv.innerHTML = "Erreur: impossible de charger Tempo";
    console.error(err);
  });
