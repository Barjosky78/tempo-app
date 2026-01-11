import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HISTORY_TEMPO_PATH = os.path.join(BASE_DIR, "history_real_tempo.json")
WEATHER_PATH = os.path.join(BASE_DIR, "weather_history.json")
RTE_PATH = os.path.join(BASE_DIR, "rte_history.json")
ENGINE_HISTORY_PATH = os.path.join(BASE_DIR, "history.json")

OUTPUT_PATH = os.path.join(BASE_DIR, "ML", "dataset_ml.json")

# =========================
# LOAD JSON SAFE
# =========================
def load_json(path):
    if not os.path.exists(path):
        print(f"⚠️ Fichier manquant : {path}")
        return []
    with open(path, "r") as f:
        return json.load(f)

tempo_real = load_json(HISTORY_TEMPO_PATH)
weather_hist = load_json(WEATHER_PATH)
rte_hist = load_json(RTE_PATH)
engine_hist = load_json(ENGINE_HISTORY_PATH)

# =========================
# INDEX BY DATE
# =========================
weather_by_date = {w["date"]: w for w in weather_hist}
rte_by_date = {r["date"]: r for r in rte_hist}
engine_by_date = {}

for h in engine_hist:
    engine_by_date.setdefault(h["date"], []).append(h)

dataset = []

# =========================
# BUILD DATASET
# =========================
for day in tempo_real:
    date = day.get("date")
    label = day.get("couleur")

    if not date or not label:
        continue

    weather = weather_by_date.get(date)
    rte = rte_by_date.get(date)
    engine_preds = engine_by_date.get(date, [])

    if not weather or not engine_preds:
        continue

    for pred in engine_preds:
        probs = pred.get("probabilites") or pred.get("probabilities")
        if not probs:
            continue

        entry = {
            "date": date,
            "label": label,
            "horizon": pred.get("horizon", 0),

            # Moteur
            "prob_rouge": probs.get("rouge", 0),
            "prob_blanc": probs.get("blanc", 0),
            "prob_bleu": probs.get("bleu", 0),

            # Météo
            "temperature": weather.get("temperature", 10),
            "cold_span": weather.get("cold_span", 0),

            # RTE
            "rte_consumption": rte.get("consommation", 55000),
            "rte_tension": rte.get("tension", 60),

            # Calendrier
            "weekday": datetime.fromisoformat(date).weekday(),
            "month": datetime.fromisoformat(date).month
        }

        dataset.append(entry)

# =========================
# SAVE
# =========================
if len(dataset) == 0:
    print("❌ Aucun échantillon généré")
    exit(1)

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

with open(OUTPUT_PATH, "w") as f:
    json.dump(dataset, f, indent=2)

print("✅ Dataset ML généré")
print("📊 Échantillons :", len(dataset))
print("📁 Fichier :", OUTPUT_PATH)
