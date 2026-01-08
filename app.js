const tempoDiv = document.getElementById("tempo");

fetch("tempo.json")
  .then(r => r.json())
  .then(raw => {

    tempoDiv.innerHTML = "";

    // 🔥 NORMALISATION FRONT (clé)
    const days = [];

    if (raw.today) days.push(raw.today);
    if (raw.tomorrow) days.push(raw.tomorrow);

    if (Array.isArray(raw.forecast)) {
      raw.forecast.forEach(d => days.push(d));
    }

    // Sécurité si déjà un tableau
    if (Array.isArray(raw)) {
      raw.forEach(d => days.push(d));
    }

    days.slice(0, 10).forEach((day, index) => {

      const div = document.createElement("div");
      div.className = "day " + day.couleur.toLowerCase();

      // 🗓️ DATE CORRECTE
      const dateObj = new Date(day.date);
      const dateTxt = dateObj.toLocaleDateString("fr-FR", {
        day: "2-digit",
        month: "2-digit"
      });

      const label =
        index === 0 ? "Aujourd’hui" :
        index === 1 ? "Demain" :
        "J+" + index;

      div.innerHTML = `
        <div class="date">${label}<br>${dateTxt}</div>
        <div><strong>${day.couleur.toUpperCase()}</strong></
