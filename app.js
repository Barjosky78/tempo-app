fetch("https://www.api-couleur-tempo.fr/api")
  .then(resp => resp.json())
  .then(data => {
    const tempo = document.getElementById("tempo");
    tempo.innerHTML = ""; // on vide avant
    // Ici data contient les jours avec date et couleur
    // Exemple format : { date: "2026-01-08", couleur: "bleu" }
    data.forEach(item => {
      const div = document.createElement("div");
      div.className = "day " + item.couleur.toLowerCase();
      div.textContent = item.date.slice(5); // mois-jour
      tempo.appendChild(div);
    });
  });
