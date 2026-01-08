const data = [
  { label: "Auj", color: "bleu" },
  { label: "Dem", color: "blanc" },
  { label: "J+2", color: "rouge" },
  { label: "J+3", color: "bleu" }
];

const tempo = document.getElementById("tempo");

data.forEach(d => {
  const div = document.createElement("div");
  div.className = `day ${d.color}`;
  div.textContent = d.label;
  tempo.appendChild(div);
});

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("service-worker.js");
}
