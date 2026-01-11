import requests
import json
from datetime import datetime

OUTPUT = "rte_history.json"

print("🔌 Téléchargement historique RTE (eco2mix national)")

URL = (
    "https://odre.opendatasoft.com/api/records/1.0/search/"
    "?dataset=eco2mix-national-cons-def"
    "&rows=10000"
    "&sort=date_heure"
)

resp = requests.get(URL)
resp.raise_for_status()

records = resp.json().get("records", [])

daily = {}

for r in records:
    fields = r.get("fields", {})
    dt = fields.get("date_heure")
    conso = fields.get("consommation")

    if not dt or conso is None:
        continue

    date = dt.split("T")[0]

    daily.setdefault(date, []).append(conso)

history = []

for date, values in daily.items():
    avg = int(sum(values) / len(values))

    if avg < 45000:
        tension = 50
    elif avg < 55000:
        tension = 60
    elif avg < 65000:
        tension = 70
    else:
        tension = 80

    history.append({
        "date": date,
        "consommation": avg,
        "tension": tension
    })

history.sort(key=lambda x: x["date"])

with open(OUTPUT, "w") as f:
    json.dump(history, f, indent=2)

print(f"✅ rte_history.json généré ({len(history)} jours)")
