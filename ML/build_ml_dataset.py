import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPO_PATH   = os.path.join(BASE_DIR, "history_real_tempo.json")
WEATHER_PATH = os.path.join(BASE_DIR, "weather_history.json")
RTE_PATH     = os.path.join(BASE_DIR, "rte_history.json")
OUT_PATH     = os.path.join(BASE_DIR, "ML", "ml_dataset.json")

# ======================
# UTILS
# ======================
def load(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def season_bounds(date):
    year = date.year if date.month >= 11 else date.year - 1
    start = datetime(year, 11, 1)
    end   = datetime(year + 1, 3, 31)
    return start, end

# ======================
# LOAD DATA
# ======================
tempo   = load(TEMPO_PATH)
weather = load(WEATHER_PATH)
rte     = load(RTE_PATH)

weather_by_date = {w["date"]: w for w in weather}
rte_by_date     = {r["date"]: r for r in rte}

# ======================
# BUILD DATASET
# ======================
MAX = { "bleu": 300, "blanc": 43, "rouge": 22 }
used_by_season = {}

dataset = []

# Trier chronologiquement (CRUCIAL)
tempo = sorted(tempo, key=lambda x: x["date"])

for t in tempo:
    date_str = t.get("date")
    color    = t.get("realColor")

    if not date_str or not color:
        continue

    if date_str not in weather_by_date:
        continue  # météo obligatoire

    date = datetime.fromisoformat(date_str)
    season_start, season_end = season_bounds(date)

    if not (season_start <= date <= season_end):
        continue  # hors saison Tempo → pas d’apprentissage

    season_key = season_start.strftime("%Y")

    if season_key not in used_by_season:
        used_by_season[season_key] = {
            "bleu": set(),
            "blanc": set(),
            "rouge": set()
        }

    used = used_by_season[season_key]

    # Marquer le jour comme consommé
    used[color].add(date_str)

    remaining = {
        "bleu":  max(0, MAX["bleu"]  - len(used["bleu"])),
        "blanc": max(0, MAX["blanc"] - len(used["blanc"])),
        "rouge": max(0, MAX["rouge"] - len(used["rouge"]))
    }

    season_day_index = (date - season_start).days + 1

    w = weather_by_date[date_str]
    r = rte_by_date.get(date_str)

    dataset.append({
        # TARGET
        "date": date_str,
        "color": color,

        # METEO
        "temperature": w.get("temperature", 10),
        "coldDays": w.get("coldDays", 0),

        # RTE
        "rteConsommation": r.get("consommation", 55000) if r else 55000,
        "rteTension": r.get("tension", 60) if r else 60,

        # TEMPO CONTEXT (NOUVEAU)
        "remainingBleu": remaining["bleu"],
        "remainingBlanc": remaining["blanc"],
        "remainingRouge": remaining["rouge"],
        "seasonDayIndex": season_day_index
    })

# ======================
# SAVE
# ======================
print(f"📊 Tempo: {len(tempo)}")
print(f"🌦️ Weather: {len(weather)}")
print(f"⚡ RTE: {len(rte)}")
print(f"✅ ML samples generated: {len(dataset)}")

if not dataset:
    raise SystemExit("❌ Aucun échantillon ML généré")

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2)

print("💾 ml_dataset.json généré avec notion de quotas Tempo")
