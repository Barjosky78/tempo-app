import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPO_PATH = os.path.join(BASE_DIR, "history_real_tempo.json")
WEATHER_PATH = os.path.join(BASE_DIR, "weather_history.json")
RTE_PATH = os.path.join(BASE_DIR, "rte_history.json")
OUT_PATH = os.path.join(BASE_DIR, "ML", "ml_dataset.json")

def load(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

tempo = load(TEMPO_PATH)
weather = load(WEATHER_PATH)
rte = load(RTE_PATH)

weather_by_date = {w["date"]: w for w in weather}
rte_by_date = {r["date"]: r for r in rte}

dataset = []

for t in tempo:
    date = t.get("date")
    color = t.get("realColor")

    if not date or not color:
        continue

    if date not in weather_by_date:
        continue  # météo obligatoire

    w = weather_by_date[date]
    r = rte_by_date.get(date)  # RTE optionnel

    dataset.append({
        "date": date,
        "color": color,   # TARGET ML

        # FEATURES
        "temperature": w.get("temperature", 10),
        "coldDays": w.get("coldDays", 0),

        "rteConsommation": r.get("consommation", 55000) if r else 55000,
        "rteTension": r.get("tension", 60) if r else 60
    })

print(f"📊 Tempo: {len(tempo)}")
print(f"🌦️ Weather: {len(weather)}")
print(f"⚡ RTE: {len(rte)}")
print(f"✅ ML samples generated: {len(dataset)}")

if not dataset:
    raise SystemExit("❌ Aucun échantillon ML généré")

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2)

print("💾 ml_dataset.json généré")
