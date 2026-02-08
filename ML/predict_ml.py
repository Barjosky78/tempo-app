"""
🤖 Prédictions ML Tempo - CORRIGÉ
Post-processing amélioré avec des probabilités plus différenciées.
"""
import json
import pandas as pd
import joblib
from datetime import datetime, date
from pathlib import Path

# ======================
# PATHS
# ======================
BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH   = BASE_DIR / "ML" / "ml_model.pkl"
TEMPO_PATH   = BASE_DIR / "tempo.json"
EDF_PATH     = BASE_DIR / "edf_tempo.json"
API_PERIOD   = BASE_DIR / "api_tempo.json"
OUTPUT_PATH  = BASE_DIR / "ML" / "ml_predictions.json"

print("🤖 Prédictions ML Tempo (post-processing amélioré)")

# ======================
# LOAD MODEL
# ======================
if not MODEL_PATH.exists():
    raise SystemExit("❌ Modèle ML introuvable")

bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
le = bundle["label_encoder"]
FEATURES = bundle["features"]
model_type = bundle.get("model_type", "Unknown")

print(f"🧠 Modèle : {model_type} | Features : {len(FEATURES)}")

COLORS = ["bleu", "blanc", "rouge"]

MAX_DAYS = {"bleu": 300, "blanc": 43, "rouge": 22}

# ======================
# LOAD DATA
# ======================
if not TEMPO_PATH.exists():
    raise SystemExit("❌ tempo.json introuvable")

tempo = json.loads(TEMPO_PATH.read_text(encoding="utf-8"))

# ======================
# COMPTEURS RÉELS DEPUIS L'API PÉRIODE
# ======================
used_days = {c: 0 for c in COLORS}

if API_PERIOD.exists():
    try:
        api_data = json.loads(API_PERIOD.read_text(encoding="utf-8"))
        if isinstance(api_data, list):
            for entry in api_data:
                lib = (entry.get("libCouleur") or "").lower().strip()
                if "bleu" in lib:
                    used_days["bleu"] += 1
                elif "blanc" in lib:
                    used_days["blanc"] += 1
                elif "rouge" in lib:
                    used_days["rouge"] += 1
            print(f"📊 Compteurs API : B={used_days['bleu']} W={used_days['blanc']} R={used_days['rouge']}")
    except Exception as e:
        print(f"⚠️ api_tempo.json illisible : {e}")

# ======================
# UTILS
# ======================
def is_winter(d: date) -> bool:
    return d.month in (11, 12, 1, 2, 3)

def is_peak_winter(d: date) -> bool:
    return d.month in (1, 2)

def get_winter_intensity(month: int) -> int:
    return {11: 2, 12: 3, 1: 4, 2: 4, 3: 2}.get(month, 0)

def get_temp_category(temp: float) -> int:
    if temp < -5: return 0
    if temp < 0: return 1
    if temp < 5: return 2
    if temp < 10: return 3
    if temp < 15: return 4
    return 5

today = date.today()
season_year = today.year if today.month >= 9 else today.year - 1
SEASON_START = date(season_year, 9, 1)

# ======================
# PREDICTIONS
# ======================
predictions = []

for day in tempo:
    if day.get("fixed"):
        continue

    try:
        d = datetime.fromisoformat(day["date"]).date()
    except Exception:
        continue

    weekday = d.weekday()

    # Quotas restants
    remaining = {c: max(0, MAX_DAYS[c] - used_days[c]) for c in COLORS}

    season_day_index = (d - SEASON_START).days + 1
    temp = day.get("temperature", 8)

    quota_pressure = (
        (43 - remaining["blanc"]) / 43 * 0.5 +
        (22 - remaining["rouge"]) / 22 * 0.5
    )

    # ======================
    # BUILD FEATURES
    # ======================
    feature_pool = {
        "temp": temp,
        "temperature": temp,
        "temp_cat": get_temp_category(temp),
        "coldDays": day.get("coldDays", 0),
        "rte": day.get("rteConsommation", 55000),
        "rteConsommation": day.get("rteConsommation", 55000),
        "weekday": weekday,
        "month": d.month,
        "day_of_month": d.day,
        "horizon": day.get("horizon", 0),
        "seasonDayIndex": season_day_index,
        "isWinter": int(is_winter(d)),
        "isWeekend": int(weekday >= 5),
        "winter_intensity": get_winter_intensity(d.month),
        "remainingBleu": remaining["bleu"],
        "remainingBlanc": remaining["blanc"],
        "remainingRouge": remaining["rouge"],
        "winterBleuRemaining": remaining["bleu"] if is_winter(d) else 0,
        "quota_pressure": quota_pressure
    }

    X = pd.DataFrame([{f: feature_pool.get(f, 0) for f in FEATURES}])

    # ======================
    # ML PREDICTION
    # ======================
    probs = model.predict_proba(X)[0]
    classes = le.inverse_transform(range(len(probs)))

    ml_probs = {c: 0.0 for c in COLORS}
    for i, c in enumerate(classes):
        ml_probs[c] = float(probs[i])

    # ======================
    # 🔒 RÈGLES EDF ABSOLUES (appliquées en premier)
    # ======================
    
    # Dimanche : TOUJOURS bleu
    if weekday == 6:
        ml_probs = {"bleu": 1.0, "blanc": 0.0, "rouge": 0.0}
    
    # Samedi : JAMAIS rouge
    elif weekday == 5:
        rouge_removed = ml_probs["rouge"]
        ml_probs["rouge"] = 0.0
        # Redistribuer proportionnellement entre bleu et blanc
        if ml_probs["bleu"] + ml_probs["blanc"] > 0:
            ratio_bleu = ml_probs["bleu"] / (ml_probs["bleu"] + ml_probs["blanc"])
            ml_probs["bleu"] += rouge_removed * ratio_bleu
            ml_probs["blanc"] += rouge_removed * (1 - ratio_bleu)
        else:
            ml_probs["bleu"] = 0.7
            ml_probs["blanc"] = 0.3
    
    # Rouge interdit hors hiver
    elif not is_winter(d):
        rouge_removed = ml_probs["rouge"]
        ml_probs["rouge"] = 0.0
        if ml_probs["bleu"] + ml_probs["blanc"] > 0:
            ratio_bleu = ml_probs["bleu"] / (ml_probs["bleu"] + ml_probs["blanc"])
            ml_probs["bleu"] += rouge_removed * ratio_bleu
            ml_probs["blanc"] += rouge_removed * (1 - ratio_bleu)

    # ======================
    # 🔥 AJUSTEMENT HIVERNAL (léger, le modèle devrait déjà gérer)
    # ======================
    if is_winter(d) and weekday not in [5, 6]:
        # Si le modèle est très confiant sur bleu en plein hiver semaine,
        # on réduit légèrement (mais le modèle entraîné avec bleu devrait être meilleur)
        if ml_probs["bleu"] > 0.7 and is_peak_winter(d):
            excess = (ml_probs["bleu"] - 0.55) * 0.3
            ml_probs["bleu"] -= excess
            ml_probs["blanc"] += excess * 0.6
            ml_probs["rouge"] += excess * 0.4
        
        # Boost température très froide
        if temp < 0:
            ml_probs["rouge"] = min(0.5, ml_probs["rouge"] * 1.3)
            ml_probs["bleu"] *= 0.85
        elif temp < 5 and is_peak_winter(d):
            ml_probs["blanc"] = min(0.5, ml_probs["blanc"] * 1.15)
            ml_probs["bleu"] *= 0.9

    # ======================
    # NORMALISATION
    # ======================
    total = sum(ml_probs.values())
    if total > 0:
        for c in COLORS:
            ml_probs[c] = ml_probs[c] / total
    else:
        if is_winter(d):
            ml_probs = {"bleu": 0.4, "blanc": 0.35, "rouge": 0.25}
        else:
            ml_probs = {"bleu": 0.85, "blanc": 0.12, "rouge": 0.03}

    # ======================
    # PLAFONNEMENT INTELLIGENT
    # Pas de 100% sauf dimanche, mais on garde la différenciation
    # ======================
    if weekday != 6:
        max_prob = max(ml_probs.values())
        if max_prob > 0.92:
            top_color = max(ml_probs, key=ml_probs.get)
            ml_probs[top_color] = 0.92
            # Redistribuer le surplus proportionnellement aux autres
            others = {c: ml_probs[c] for c in COLORS if c != top_color}
            others_total = sum(others.values())
            surplus = 1.0 - 0.92 - others_total
            if others_total > 0:
                for c in others:
                    ml_probs[c] += surplus * (others[c] / others_total)
            else:
                # Distribuer uniformément
                for c in others:
                    ml_probs[c] = (1.0 - 0.92) / len(others)

    # Re-normaliser après plafonnement
    total = sum(ml_probs.values())
    if total > 0 and abs(total - 1.0) > 0.01:
        for c in COLORS:
            ml_probs[c] /= total

    ml_color = max(ml_probs, key=ml_probs.get)

    predictions.append({
        "date": day["date"],
        "mlPrediction": ml_color,
        "mlProbabilities": {c: round(ml_probs[c] * 100) for c in COLORS},
        "mlConfidence": round(ml_probs[ml_color] * 100)
    })

    print(f"  {day['date']} ({['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'][weekday]}) "
          f"→ {ml_color.upper()} "
          f"(B:{round(ml_probs['bleu']*100)}% W:{round(ml_probs['blanc']*100)}% R:{round(ml_probs['rouge']*100)}%)")

# ======================
# SAVE
# ======================
OUTPUT_PATH.parent.mkdir(exist_ok=True)
OUTPUT_PATH.write_text(json.dumps(predictions, indent=2), encoding="utf-8")

print(f"\n✅ {len(predictions)} prédictions ML générées")
for color in COLORS:
    count = sum(1 for p in predictions if p["mlPrediction"] == color)
    print(f"   {color}: {count}")
