"""
📊 Construction dataset ML Tempo - CORRIGÉ
Inclut les 3 couleurs (bleu, blanc, rouge) pour un entraînement équilibré.
"""
import json
import os
from datetime import datetime
from collections import Counter

# ======================
# PATHS
# ======================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPO_PATH   = os.path.join(BASE_DIR, "history_real_tempo.json")
WEATHER_PATH = os.path.join(BASE_DIR, "weather_history.json")
RTE_PATH     = os.path.join(BASE_DIR, "rte_history.json")
OUT_PATH     = os.path.join(BASE_DIR, "ML", "ml_dataset.json")

print("📊 Construction dataset ML Tempo (3 couleurs : bleu + blanc + rouge)")

# ======================
# CONSTANTES TEMPO
# ======================
MAX_DAYS = {"bleu": 300, "blanc": 43, "rouge": 22}
COLOR_PRIORITY = {"rouge": 3, "blanc": 2, "bleu": 1}

# ======================
# UTILS
# ======================
def load(path):
    if not os.path.exists(path):
        print(f"⚠️ Fichier non trouvé : {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def tempo_season_bounds(dt: datetime):
    year = dt.year if dt.month >= 9 else dt.year - 1
    return datetime(year, 9, 1), datetime(year + 1, 8, 31)

def is_winter(dt: datetime) -> bool:
    return dt.month in (11, 12, 1, 2, 3)

def is_peak_winter(dt: datetime) -> bool:
    return dt.month in (1, 2)

def compute_temp_category(temp: float) -> int:
    if temp < -5: return 0
    if temp < 0: return 1
    if temp < 5: return 2
    if temp < 10: return 3
    if temp < 15: return 4
    return 5

def get_winter_intensity(month: int) -> int:
    return {11: 2, 12: 3, 1: 4, 2: 4, 3: 2}.get(month, 0)

def compute_energy_stress(consumption: int) -> int:
    if consumption >= 60000: return 3
    elif consumption >= 52000: return 2
    elif consumption >= 45000: return 1
    return 0

# ======================
# LOAD DATA
# ======================
tempo_raw = load(TEMPO_PATH)
weather   = load(WEATHER_PATH)
rte       = load(RTE_PATH)

print(f"📅 Tempo brut : {len(tempo_raw)} entrées")
print(f"🌦️ Weather : {len(weather)} entrées")
print(f"⚡ RTE : {len(rte)} entrées")

# Vérification critique : présence de jours bleu
color_check = Counter(
    (e.get("color") or e.get("realColor", "")).lower()
    for e in tempo_raw
)
print(f"📈 Distribution brute : {dict(color_check)}")

if color_check.get("bleu", 0) == 0:
    print("❌ ERREUR CRITIQUE : Aucun jour bleu dans history_real_tempo.json !")
    print("   → Exécutez d'abord build_history_from_tempo_api.py pour récupérer")
    print("     l'historique complet avec les jours bleu depuis l'API EDF.")
    raise SystemExit("Dataset incomplet : pas de jours bleu")

weather_by_date = {w["date"]: w for w in weather if isinstance(w, dict) and "date" in w}
rte_by_date = {r["date"]: r for r in rte if isinstance(r, dict) and "date" in r}

# ======================
# DÉDUPLICATION TEMPO
# ======================
tempo_by_date = {}

for entry in tempo_raw:
    d = entry.get("date")
    c = (entry.get("color") or entry.get("realColor", "")).lower().strip()
    
    if not d or c not in COLOR_PRIORITY:
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
        dt = datetime.fromisoformat(date_str)
    except ValueError:
        continue

    season_start, season_end = tempo_season_bounds(dt)
    if not (season_start <= dt <= season_end):
        continue

    season_key = season_start.strftime("%Y")

    if season_key not in used_by_season:
        used_by_season[season_key] = {"bleu": set(), "blanc": set(), "rouge": set()}

    used = used_by_season[season_key]

    # Règles EDF : rouge interdit hors hiver et samedi
    if color == "rouge" and not is_winter(dt):
        continue
    if color == "rouge" and dt.weekday() == 5:
        continue

    used[color].add(date_str)

    remaining_bleu  = max(0, MAX_DAYS["bleu"]  - len(used["bleu"]))
    remaining_blanc = max(0, MAX_DAYS["blanc"] - len(used["blanc"]))
    remaining_rouge = max(0, MAX_DAYS["rouge"] - len(used["rouge"]))

    season_day_index = (dt - season_start).days + 1

    # Données météo
    w = weather_by_date.get(date_str, {})
    temp = w.get("temperature", 10)

    # Données RTE
    r = rte_by_date.get(date_str, {})
    consommation = r.get("consommation", 55000)

    sample = {
        "date": date_str,
        "color": color,

        # Calendrier
        "weekday": dt.weekday(),
        "month": dt.month,
        "day_of_month": dt.day,
        "seasonDayIndex": season_day_index,
        "isWeekend": int(dt.weekday() >= 5),
        "isWinter": int(is_winter(dt)),
        "isPeakWinter": int(is_peak_winter(dt)),
        "winter_intensity": get_winter_intensity(dt.month),

        # Météo
        "temp": temp,
        "temperature": temp,
        "temp_cat": compute_temp_category(temp),
        "coldDays": w.get("coldDays", 0),

        # Énergie
        "rte": consommation,
        "rteConsommation": consommation,
        "energyStress": compute_energy_stress(consommation),

        # Quotas Tempo
        "remainingBleu": remaining_bleu,
        "remainingBlanc": remaining_blanc,
        "remainingRouge": remaining_rouge,
        "winterBleuRemaining": remaining_bleu if is_winter(dt) else 0,

        # Ratios
        "blancUsageRatio": round((43 - remaining_blanc) / 43, 3),
        "rougeUsageRatio": round((22 - remaining_rouge) / 22, 3),
        "quota_pressure": round(
            (43 - remaining_blanc) / 43 * 0.5 +
            (22 - remaining_rouge) / 22 * 0.5, 3
        ),

        "horizon": 0
    }

    dataset.append(sample)

# ======================
# STATISTIQUES
# ======================
print(f"\n✅ Dataset généré : {len(dataset)} échantillons")

if dataset:
    colors = Counter(s["color"] for s in dataset)
    print("\n📈 Distribution des couleurs :")
    for c, n in colors.most_common():
        pct = n / len(dataset) * 100
        print(f"   {c}: {n} ({pct:.1f}%)")

    # Vérification qualité
    if colors.get("bleu", 0) < 50:
        print(f"\n⚠️ Seulement {colors.get('bleu', 0)} jours bleu - le modèle risque d'être biaisé")
    
    print("\n📅 Par saison :")
    for season, used in sorted(used_by_season.items()):
        total = sum(len(v) for v in used.values())
        print(f"   {season}-{int(season)+1}: {total} jours " +
              f"(B:{len(used['bleu'])} W:{len(used['blanc'])} R:{len(used['rouge'])})")

# ======================
# SAVE
# ======================
if not dataset:
    raise SystemExit("❌ Aucun échantillon ML généré")

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2)

print(f"\n💾 Sauvegardé : {OUT_PATH}")
print("🎉 Dataset ML avec les 3 couleurs prêt !")
