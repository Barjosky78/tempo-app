import json
import os
from datetime import datetime

# ======================
# PATHS
# ======================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPO_PATH   = os.path.join(BASE_DIR, "history_real_tempo.json")
WEATHER_PATH = os.path.join(BASE_DIR, "weather_history.json")
RTE_PATH     = os.path.join(BASE_DIR, "rte_history.json")
OUT_PATH     = os.path.join(BASE_DIR, "ML", "ml_dataset.json")

# ======================
# CONSTANTES TEMPO
# ======================
MAX_DAYS = {
    "bleu": 85,     # ⚠️ PÉRIODE TEMPO ≈ 150 jours
    "blanc": 43,
    "rouge": 22
}

COLOR_TO_STRESS = {
    "bleu": 1,
    "blanc": 2,
    "rouge": 3
}

# ======================
# UTILS
# ======================
def load(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def is_winter(date: datetime) -> bool:
    return date.month in (11, 12, 1, 2, 3)

def tempo_season_start(date: datetime):
    year = date.year if date.month >= 9 else date.year - 1
    return datetime(year, 9, 1)

# ======================
# LOAD DATA
# ======================
tempo   = load(TEMPO_PATH)
weather = load(WEATHER_PATH)
rte     = load(RTE_PATH)

weather_by_date = {w["date"]: w for w in weather if "date" in w}
rte_by_date     = {r["date"]: r for r in rte if "date" in r}

# ======================
# BUILD DATASET
# ======================
dataset = []
used = {"bleu": set(), "blanc": set(), "rouge": set()}

tempo = sorted(tempo, key=lambda x: x.get("date", ""))

for t in tempo:
    date_str = t.get("date")
    color = t.get("color")

    if not date_str or color not in COLOR_TO_STRESS:
        continue
    if date_str not in weather_by_date:
        continue

    try:
        d = datetime.fromisoformat(date_str)
    except Exception:
        continue

    if color == "rouge" and not is_winter(d):
        continue

    used[color].add(date_str)

    remaining = {
        "bleu":  max(0, MAX_DAYS["bleu"]  - len(used["bleu"])),
        "blanc": max(0, MAX_DAYS["blanc"] - len(used["blanc"])),
        "rouge": max(0, MAX_DAYS["rouge"] - len(used["rouge"]))
    }

    season_day_index = (d - tempo_season_start(d)).days + 1

    w = weather_by_date[date_str]
    r = rte_by_date.get(date_str, {})

    dataset.append({
        "date": date_str,

        # FEATURES
        "temperature": w.get("temperature", 10),
        "coldDays": w.get("coldDays", 0),
        "rteConsommation": r.get("consommation", 55000),
        "weekday": d.weekday(),
        "month": d.month,
        "isWinter": int(is_winter(d)),
        "seasonDayIndex": season_day_index,

        "remainingBlanc": remaining["blanc"],
        "remainingRouge": remaining["rouge"],

        # TARGET ML
        "stressLevel": COLOR_TO_STRESS[color],

        # debug only
        "realColor": color
    })

# ======================
# SAVE
# ======================
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2)

print(f"✅ Dataset ML généré : {len(dataset)} lignes")
