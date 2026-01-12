import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPO_PATH = os.path.join(BASE_DIR, "history_real_tempo.json")
WEATHER_PATH = os.path.join(BASE_DIR, "weather_history.json")
RTE_PATH = os.path.join(BASE_DIR, "rte_history.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "ML", "ml_dataset.json")

# ======================
# LOAD FILES
# ======================
def load_json(path):
    if not os.path.exists(path):
        print("❌ Fichier manquant:", path)
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

tempo = load_json(TEMPO_PATH)
weather = load_json(WEATHER_PATH)
rte = load_json(RTE_PATH)

print(f"📊 Tempo: {len(tempo)}")
print(f"🌦️ Weather: {len(weather)}")
print(f"⚡ RTE: {len(rte)}")

# ======================
# INDEX PAR DATE
# ======================
weather_by_date = {w["date"][:10]: w for w in weather if "date" in w}
rte_by_date = {r["date"][:10]: r for r in rte if "date" in r}

dataset = []

# ======================
# BUILD DATASET
# ======================
for h in tempo:
    date = h.get("date") or h.get("jour") or h.get("day")
    if not date:
        continue

    date = date[:10]

    # 🎯 COULEUR TEMPO (robuste)
    couleur = (
        h.get("couleur")
        or h.get("color")
        or h.get("tempo")
        or h.get("value")
    )

    if couleur not in ("bleu", "blanc", "rouge"):
        continue

    w = weather_by_date.get(date, {})
    r = rte_by_date.get(date, {})

    try:
        d = datetime.fromisoformat(date)
    except:
        continue

    sample = {
        "date": date,

        # FEATURES
        "temperature": w.get("temperature", w.get("temp", 8)),
        "weekday": d.weekday(),
        "month": d.month,
        "rteConsommation": r.get("consommation", 55000),
        "rteTension": r.get("tension", 60),

        # LABEL
        "label": couleur
    }

    dataset.append(sample)

# ======================
# SAVE
# ======================
if not dataset:
    print("❌ Aucun échantillon généré")
    exit(1)

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2)

print("✅ Dataset ML généré")
print("📦 Échantillons:", len(dataset))
print("📁 Fichier:", OUTPUT_PATH)
