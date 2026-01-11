import requests
import json
from datetime import datetime

URL = "https://www.api-couleur-tempo.fr/api/tempo"
OUTPUT = "history_real_tempo.json"

print("📡 Téléchargement historique Tempo EDF…")

resp = requests.get(URL, timeout=30)
resp.raise_for_status()

data = resp.json()

history = []

for item in data:
    date = item.get("date")
    color = item.get("couleur")

    if not date or not color:
        continue

    history.append({
        "date": date,
        "realColor": color.lower(),
        "source": "api-couleur-tempo.fr",
        "generatedAt": datetime.utcnow().isoformat()
    })

history.sort(key=lambda x: x["date"])

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(history, f, indent=2, ensure_ascii=False)

print(f"✅ {len(history)} jours Tempo enregistrés dans {OUTPUT}")
