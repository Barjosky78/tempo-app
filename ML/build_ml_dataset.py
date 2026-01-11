import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPO_PATH = os.path.join(BASE_DIR, "history_real_tempo.json")
WEATHER_PATH = os.path.join(BASE_DIR, "weather_history.json")
RTE_PATH = os.path.join(BASE_DIR, "rte_history.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "ML", "ml_dataset.json")

def load_json(path):
    if not os.path.exists(path):
        print(f"❌ Fichier manquant : {path}")
        return []
    with open(path, "r") as f:
        return json.load(f)

print("📦 Chargement des historiques…")

tempo = load_json(TEMPO_PATH)
weather = load_json(WEATHER_PATH)
rte = load_json(RTE_PATH)

# Index par date
weather_by_date = {d["date"]: d for d in weather}
rte_by_date = {d["date"]: d for d in rte}

dataset = []

for day in tempo:
    date = day.get("date")
    color = day.get("color") or day.get("couleur")

    if not date or not color:
        continue

    w = weather_by_date.get(date)
    r = rte_by_date.get(date)

    if not w or not r:
        continue  # on garde seulement les jours complets

    dt = datetime.fromisoformat(date)

    sample = {
        "date": date,
        "target_color": color,              # 🎯 target ML
        "temperature": w.get("temperature"),
        "consommation": r.get("consommation"),
        "tension": r.get("tension"),
        "weekday": dt.weekday(),             # 0=lundi
        "month": dt.month
    }

    dataset.append(sample)

print(f"✅ Dataset ML créé : {len(dataset)} lignes")

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

with open(OUTPUT_PATH, "w") as f:
    json.dump(dataset, f, indent=2)

print(f"💾 Fichier généré : {OUTPUT_PATH}")
