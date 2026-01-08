const tempoDiv = document.getElementById("tempo");

fetch("tempo.json")
  .then(r => r.json())
  .then(data => {
    tempoDiv.innerHTML = "";
    data.forEach((day, index) => {
      const div = document.createElement("div");
      div.className = "day " + day.couleur.toLowerCase();
      const label = index === 0 ? "Aujourd'hui" : index === 1 ? "Demain" : "J+" + index;
      div.innerHTML = `
        <div class="date">${label}<br>${day.date.slice(8,10)}/${day.date.slice(5,7)}</div>
        <div><strong>${day.couleur.toUpperCase()}</strong></div>
        <div class="proba">
          🔴 ${day.probabilites.rouge} %<br>
          ⚪ ${day.probabilites.blanc} %<br>
          🔵 ${day.probabilites.bleu} %
        </div>
      `;
      tempoDiv.appendChild(div);
    });
  })
  .catch(err => {
    tempoDiv.innerHTML = "Erreur: impossible de charger Tempo";
    console.error(err);
  });
