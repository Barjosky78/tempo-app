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

def compute_energy_stress(consumption: int) -> int:
    """
    Stress énergétique explicite pour la ML
    0 = très faible
    1 = normal
    2 = tendu
    3 = critique
    """
    if consumption >= 65000:
        return 3
    elif consumption >= 58000:
        return 2
    elif consumption >= 52000:
        return 1
    return 0

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
# ======================
tempo_by_date = {}

for entry in tempo_raw:
    d = entry.get("date")
    c = entry.get("color")

    if not d or not c:
        continue

    if d not in tempo_by_date or COLOR_PRIORITY[c] > COLOR_PRIORITY[tempo_by_date[d]]:
        tempo_by_date[d] = c

# ======================
# BUILD DATASET ML
# ======================
dataset = []
used_by_season = {}

for date_str in sorted(tempo_by_date.keys()):
    color = tempo_by_date[date_str]

    if date_str not in weather_by_date:
        continue

    try:
        date = datetime.fromisoformat(date_str)
    except ValueError:
        continue

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

    consommation = r.get("consommation", 55000)
    energy_stress = compute_energy_stress(consommation)

    # 🔑 stress tempo progressif (0 → 1)
    tempo_stress_ratio = 1 - (remaining_tempo_days / TEMPO_TOTAL_DAYS)

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
        "rteConsommation": consommation,
        "rteTension": r.get("tension", 60),
        "energyStress": energy_stress,

        # ======================
        # CONTEXTE TEMPO (CLÉ ML)
        # ======================
        "remainingBleu": remaining_bleu,
        "remainingBlanc": remaining_blanc,
        "remainingRouge": remaining_rouge,
        "remainingTempoDays": remaining_tempo_days,
        "tempoStressRatio": round(tempo_stress_ratio, 3),

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

print("💾 ml_dataset.json généré (stress Tempo + stress énergétique intégrés)")
