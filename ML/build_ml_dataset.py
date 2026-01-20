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

print("📊 Construction dataset ML Tempo OPTIMISÉ")

# ======================
# CONSTANTES TEMPO (RÈGLES OFFICIELLES EDF)
# ======================
# Saison Tempo : 1er sept → 31 août
# 300 jours bleu, 43 jours blanc, 22 jours rouge = 365 jours
MAX_DAYS = {
    "bleu": 300,
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
        print(f"⚠️ Fichier non trouvé : {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def tempo_season_bounds(date: datetime):
    """Retourne les bornes de la saison Tempo"""
    year = date.year if date.month >= 9 else date.year - 1
    return datetime(year, 9, 1), datetime(year + 1, 8, 31)

def is_winter(date: datetime) -> bool:
    """Période où blanc/rouge sont possibles"""
    return date.month in (11, 12, 1, 2, 3)

def is_peak_winter(date: datetime) -> bool:
    """Période pic hiver (janvier/février)"""
    return date.month in (1, 2)

def is_red_allowed(date: datetime) -> bool:
    """Rouge uniquement en hiver"""
    return is_winter(date)

def compute_energy_stress(consumption: int) -> int:
    """
    Niveau de stress énergétique
    0 = très faible (<45000 MW)
    1 = normal (45-52k MW)
    2 = tendu (52-60k MW)
    3 = critique (>60k MW)
    """
    if consumption >= 60000:
        return 3
    elif consumption >= 52000:
        return 2
    elif consumption >= 45000:
        return 1
    return 0

def compute_temp_category(temp: float) -> int:
    """
    Catégorie de température
    0 = très froid (<-5°C)
    1 = froid (-5 à 0°C)
    2 = frais (0 à 5°C)
    3 = doux (5 à 10°C)
    4 = modéré (10 à 15°C)
    5 = chaud (>15°C)
    """
    if temp < -5: return 0
    if temp < 0: return 1
    if temp < 5: return 2
    if temp < 10: return 3
    if temp < 15: return 4
    return 5

def get_winter_intensity(month: int) -> int:
    """Intensité de l'hiver par mois"""
    return {11: 2, 12: 3, 1: 4, 2: 4, 3: 2}.get(month, 0)

# ======================
# LOAD DATA
# ======================
tempo_raw = load(TEMPO_PATH)
weather   = load(WEATHER_PATH)
rte       = load(RTE_PATH)

print(f"📅 Tempo brut : {len(tempo_raw)} entrées")
print(f"🌦️ Weather : {len(weather)} entrées")
print(f"⚡ RTE : {len(rte)} entrées")

weather_by_date = {
    w["date"]: w for w in weather
    if isinstance(w, dict) and "date" in w
}

rte_by_date = {
    r["date"]: r for r in rte
    if isinstance(r, dict) and "date" in r
}

# ======================
# DÉDUPLICATION TEMPO (garder la couleur la plus "grave")
# ======================
tempo_by_date = {}

for entry in tempo_raw:
    d = entry.get("date")
    c = entry.get("color")

    if not d or not c:
        continue

    c = c.lower()
    if c not in COLOR_PRIORITY:
        continue

    if d not in tempo_by_date or COLOR_PRIORITY[c] > COLOR_PRIORITY[tempo_by_date[d]]:
        tempo_by_date[d] = c

print(f"📅 Tempo dédupliqué : {len(tempo_by_date)} jours uniques")

# ======================
# BUILD DATASET ML
# ======================
dataset = []
used_by_season = {}

for date_str in sorted(tempo_by_date.keys()):
    color = tempo_by_date[date_str]

    try:
        date = datetime.fromisoformat(date_str)
    except ValueError:
        continue

    # Vérifier que dans une saison Tempo valide
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

    # ❌ Ignorer rouge hors hiver (données incorrectes)
    if color == "rouge" and not is_red_allowed(date):
        print(f"⚠️ Ignoré : rouge le {date_str} (hors hiver)")
        continue

    # ❌ Ignorer rouge le samedi (règle EDF)
    if color == "rouge" and date.weekday() == 5:
        print(f"⚠️ Ignoré : rouge le samedi {date_str}")
        continue

    used[color].add(date_str)

    # Quotas restants
    remaining_bleu  = max(0, MAX_DAYS["bleu"]  - len(used["bleu"]))
    remaining_blanc = max(0, MAX_DAYS["blanc"] - len(used["blanc"]))
    remaining_rouge = max(0, MAX_DAYS["rouge"] - len(used["rouge"]))

    season_day_index = (date - season_start).days + 1

    # Données météo
    w = weather_by_date.get(date_str, {})
    temp = w.get("temperature", 10)

    # Données RTE
    r = rte_by_date.get(date_str, {})
    consommation = r.get("consommation", 55000)

    # ======================
    # FEATURES
    # ======================
    sample = {
        # === TARGET ===
        "date": date_str,
        "color": color,

        # === CALENDRIER ===
        "weekday": date.weekday(),
        "month": date.month,
        "day_of_month": date.day,
        "seasonDayIndex": season_day_index,
        "isWeekend": int(date.weekday() >= 5),
        "isMonday": int(date.weekday() == 0),
        "isFriday": int(date.weekday() == 4),

        # === SAISON ===
        "isWinter": int(is_winter(date)),
        "isPeakWinter": int(is_peak_winter(date)),
        "winter_intensity": get_winter_intensity(date.month),

        # === MÉTÉO ===
        "temp": temp,
        "temperature": temp,  # Alias pour compatibilité
        "temp_cat": compute_temp_category(temp),
        "coldDays": w.get("coldDays", 0),

        # === ÉNERGIE ===
        "rte": consommation,
        "rteConsommation": consommation,  # Alias
        "energyStress": compute_energy_stress(consommation),

        # === QUOTAS TEMPO ===
        "remainingBleu": remaining_bleu,
        "remainingBlanc": remaining_blanc,
        "remainingRouge": remaining_rouge,
        "winterBleuRemaining": remaining_bleu if is_winter(date) else 0,

        # === RATIOS ===
        "blancUsageRatio": round((43 - remaining_blanc) / 43, 3),
        "rougeUsageRatio": round((22 - remaining_rouge) / 22, 3),
        "quota_pressure": round(
            (43 - remaining_blanc) / 43 * 0.5 +
            (22 - remaining_rouge) / 22 * 0.5, 3
        ),

        # === HORIZON (pour compatibilité prédiction) ===
        "horizon": 0
    }

    dataset.append(sample)

# ======================
# STATISTIQUES
# ======================
print(f"\n✅ Dataset généré : {len(dataset)} échantillons")

if dataset:
    from collections import Counter
    colors = Counter(s["color"] for s in dataset)
    print("\n📈 Distribution des couleurs :")
    for c, n in colors.most_common():
        pct = n / len(dataset) * 100
        print(f"   {c}: {n} ({pct:.1f}%)")

    # Distribution par saison
    print("\n📅 Par saison :")
    for season, used in used_by_season.items():
        total = sum(len(v) for v in used.values())
        print(f"   {season}-{int(season)+1}: {total} jours")
        for c in ["bleu", "blanc", "rouge"]:
            print(f"      {c}: {len(used[c])}")

# ======================
# SAVE
# ======================
if not dataset:
    raise SystemExit("❌ Aucun échantillon ML généré")

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2)

print(f"\n💾 Sauvegardé : {OUT_PATH}")
print("🎉 Dataset ML optimisé prêt pour l'entraînement !")
