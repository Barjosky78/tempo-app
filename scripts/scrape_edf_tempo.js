const https = require("https");

const EDF_URL =
  "https://particulier.edf.fr/fr/accueil/gestion-contrat/options/tempo.html";

function fetchHTML(url) {
  return new Promise((resolve, reject) => {
    https.get(url, res => {
      let data = "";
      res.on("data", c => (data += c));
      res.on("end", () => resolve(data));
    }).on("error", reject);
  });
}

function extractColor(text) {
  text = text.toLowerCase();
  if (text.includes("bleu")) return "bleu";
  if (text.includes("blanc")) return "blanc";
  if (text.includes("rouge")) return "rouge";
  return null;
}

(async () => {
  try {
    const html = await fetchHTML(EDF_URL);

    const todayMatch = html.match(/Aujourd['’]hui[^<]*<\/span>\s*<span[^>]*>(.*?)<\/span>/i);
    const tomorrowMatch = html.match(/Demain[^<]*<\/span>\s*<span[^>]*>(.*?)<\/span>/i);

    const today = todayMatch ? extractColor(todayMatch[1]) : null;
    const tomorrow = tomorrowMatch ? extractColor(tomorrowMatch[1]) : null;

    const result = {
      source: "edf.fr",
      fetchedAt: new Date().toISOString(),
      today,
      tomorrow
    };

    console.log(JSON.stringify(result, null, 2));
  } catch (e) {
    console.error(JSON.stringify({
      source: "edf.fr",
      error: e.message
    }));
    process.exit(1);
  }
})();
