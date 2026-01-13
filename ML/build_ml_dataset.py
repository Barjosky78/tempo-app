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
# CONSTANTES TEMPO (LOGIQUE EDF OFFICIELLE)
# ======================
TEMPO_TOTAL_DAYS = 150

MAX_DAYS = {
    "bleu": 85,
    "blanc": 43,
    "rouge": 22
}

COLOR_PRIORITY = {
    "rouge": 3,
    "blanc": 2,
    "bleu": 1
}

# ======================
# UTILS
# ======================
def load(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def tempo_season_bounds(date: datetime):
    year = date.year if date.month >= 9 else date.year - 1
    return datetime(year, 9, 1), datetime(year + 1, 8, 31)

def is_winter(date: datetime) -> bool:
    return date.month in (11, 12, 1, 2, 3)

def is_red_allowed(date: datetime) -> bool:
    return is_winter(date)

# ======================
# LOAD DATA
# ======================
tempo_raw = load(TEMPO_PATH)
weather   = load(WEATHER_PATH)
rte       = load(RTE_PATH)

weather_by_date = {
    w["date"]: w for w in weather
    if isinstance(w, dict) and "date" in w
}

rte_by_date = {
    r["date"]: r for r in rte
    if isinstance(r, dict) and "date" in r
}

# ======================
# DÉDUPLICATION TEMPO
# 1 date = 1 couleur (priorité rouge > blanc > bleu)
# ======================
tempo_by_date = {}

for entry in tempo_raw:
    date = entry.get("date")
    color = entry.get("color")

    if not date or not color:
        continue

    if (
        date not in tempo_by_date
        or COLOR_PRIORITY[color] > COLOR_PRIORITY[tempo_by_date[date]]
    ):
        tempo_by_date[date] = color

# ======================
# BUILD DATASET ML
# ======================
dataset = []
used_by_season = {}

for date_str in sorted(tempo_by_date.keys()):
    color = tempo_by_date[date_str]

    if date_str not in weather_by_date:
        continue  # météo obligatoire pour ML

    try:
        date = datetime.fromisoformat(date_str)
    except ValueError:
        continue

    # ======================
    # SAISON TEMPO
    # ======================
    season_start, season_end = tempo_season_bounds(date)
    if not (season_start <= date <= season_end):
        continue

    season_key = season_start.strftime("%Y")

    if season_key not in used_by_season:
        used_by_season[season_key] = {
            "bleu": set(),
            "blanc": set(),
            "rouge": set()
        }

    used = used_by_season[season_key]

    # ❌ Rouge interdit hors hiver
    if color == "rouge" and not is_red_allowed(date):
        continue

    # ======================
    # CONSOMMATION DU JOUR
    # ======================
    used[color].add(date_str)

    remaining_bleu  = max(0, MAX_DAYS["bleu"]  - len(used["bleu"]))
    remaining_blanc = max(0, MAX_DAYS["blanc"] - len(used["blanc"]))
    remaining_rouge = max(0, MAX_DAYS["rouge"] - len(used["rouge"]))

    remaining_tempo_days = (
        remaining_bleu + remaining_blanc + remaining_rouge
    )

    season_day_index = (date - season_start).days + 1

    w = weather_by_date.get(date_str, {})
    r = rte_by_date.get(date_str, {})

    dataset.append({
        # ======================
        # TARGET
        # ======================
        "date": date_str,
        "color": color,

        # ======================
        # METEO
        # ======================
        "temperature": w.get("temperature", 10),
        "coldDays": w.get("coldDays", 0),

        # ======================
        # RTE
        # ======================
        "rteConsommation": r.get("consommation", 55000),
        "rteTension": r.get("tension", 60),

        # ======================
        # CONTEXTE TEMPO (🔥 CLÉ ML)
        # ======================
        "remainingBleu": remaining_bleu,
        "remainingBlanc": remaining_blanc,
        "remainingRouge": remaining_rouge,
        "remainingTempoDays": remaining_tempo_days,

        "winterBleuRemaining": remaining_bleu if is_winter(date) else 0,
        "seasonDayIndex": season_day_index,
        "isWinter": int(is_winter(date))
    })

# ======================
# SAVE
# ======================
print(f"📊 Tempo brut           : {len(tempo_raw)}")
print(f"📅 Tempo dédupliqué     : {len(tempo_by_date)}")
print(f"🌦️ Weather records      : {len(weather)}")
print(f"⚡ RTE records          : {len(rte)}")
print(f"✅ ML samples generated : {len(dataset)}")

if not dataset:
    raise SystemExit("❌ Aucun échantillon ML généré")

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2)

print("💾 ml_dataset.json généré (logique Tempo 150 jours correcte)")
