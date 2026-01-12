import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPO_PATH = os.path.join(BASE_DIR, "history_real_tempo.json")
WEATHER_PATH = os.path.join(BASE_DIR, "weather_history.json")
RTE_PATH = os.path.join(BASE_DIR, "rte_history.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "ML", "ml_dataset.json")

# ======================
# LOAD FILES (SAFE)
# ======================
def load_json(path):
    if not os.path.exists(path):
        print("❌ Fichier manquant :", path)
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

tempo = load_json(TEMPO_PATH)
weather = load_json(WEATHER_PATH)
rte = load_json(RTE_PATH)

print("📊 Tempo:", len(tempo))
print("🌦️ Weather:", len(weather))
print("⚡ RTE:", len(rte))

# ======================
# INDEX PAR DATE
# ======================
weather_by_date = {
    w["date"]: w for w in weather
    if "date" in w
}

rte_by_date = {
    r["date"]: r for r in rte
    if "date" in r
}

dataset = []

# ======================
# BUILD DATASET
# ======================
for h in tempo:
    date = h.get("date")
    couleur = h.get("couleur")  # ⚠️ PAS realColor

    if not date or not couleur:
        continue

    w = weather_by_date.get(date)
    r = rte_by_date.get(date)

    # --- FEATURES ---
    temperature = w.get("temperature", 8) if w else 8
    consommation = r.get("consommation", 55000) if r else 55000
    tension = r.get("tension", 60) if r else 60

    d = datetime.fromisoformat(date)

    sample = {
        "date": date,

        # FEATURES
        "temperature": temperature,
        "weekday": d.weekday(),
        "month": d.month,
        "rteConsommation": consommation,
        "rteTension": tension,

        # LABEL
        "label": couleur
    }

    dataset.append(sample)

# ======================
# SAVE
# ======================
if len(dataset) == 0:
    print("❌ Aucun échantillon généré")
    exit(1)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2)

print("✅ Dataset ML généré")
print("📦 Échantillons :", len(dataset))
print("📁 Fichier :", OUTPUT_PATH)
