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
HISTORY_PATH = BASE_DIR / "history.json"
OUTPUT_PATH  = BASE_DIR / "ML" / "ml_predictions.json"

print("🤖 Prédictions ML Tempo OPTIMISÉES (boost hivernal + règles EDF)")

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

print(f"🧠 Modèle chargé : {model_type}")
print(f"🧠 Features attendues : {FEATURES}")

COLORS = ["bleu", "blanc", "rouge"]

# ======================
# CONSTANTES TEMPO
# ======================
MAX_DAYS = {
    "bleu": 300,
    "blanc": 43,
    "rouge": 22
}

# ======================
# LOAD DATA
# ======================
if not TEMPO_PATH.exists():
    raise SystemExit("❌ tempo.json introuvable")

tempo = json.loads(TEMPO_PATH.read_text(encoding="utf-8"))

# ======================
# LOAD HISTORY (quotas réels)
# ======================
used_days = {c: set() for c in COLORS}

if HISTORY_PATH.exists():
    try:
        history = json.loads(HISTORY_PATH.read_text(encoding="utf-8") or "[]")
        for h in history:
            c = h.get("realColor")
            d = h.get("date")
            if c in used_days and d:
                used_days[c].add(d)
    except Exception as e:
        print(f"⚠️ history.json invalide → quotas ignorés : {e}")

# ======================
# UTILS
# ======================
def is_winter(d: date) -> bool:
    """Mois où blanc/rouge sont probables"""
    return d.month in (11, 12, 1, 2, 3)

def is_peak_winter(d: date) -> bool:
    """Mois où rouge est très probable (janvier/février)"""
    return d.month in (1, 2)

def red_allowed(d: date) -> bool:
    """Rouge uniquement en hiver"""
    return is_winter(d)

def get_winter_intensity(month: int) -> int:
    """Intensité de l'hiver par mois"""
    return {11: 2, 12: 3, 1: 4, 2: 4, 3: 2}.get(month, 0)

def get_temp_category(temp: float) -> int:
    """Catégorie de température"""
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

    # ❌ Pas de ML sur jours EDF officiels
    if day.get("fixed"):
        continue

    try:
        d = datetime.fromisoformat(day["date"]).date()
    except Exception:
        continue

    weekday = d.weekday()

    # ======================
    # QUOTAS RESTANTS
    # ======================
    remaining_bleu  = max(0, MAX_DAYS["bleu"]  - len(used_days["bleu"]))
    remaining_blanc = max(0, MAX_DAYS["blanc"] - len(used_days["blanc"]))
    remaining_rouge = max(0, MAX_DAYS["rouge"] - len(used_days["rouge"]))

    season_day_index = (d - SEASON_START).days + 1
    
    # Pression des quotas (fin de saison)
    quota_pressure = (
        (43 - remaining_blanc) / 43 * 0.5 +
        (22 - remaining_rouge) / 22 * 0.5
    )

    temp = day.get("temperature", 8)

    # ======================
    # FEATURE POOL COMPLET (compatible avec les deux modèles)
    # ======================
    feature_pool = {
        # Météo
        "temp": temp,
        "temperature": temp,
        "temp_cat": get_temp_category(temp),
        "coldDays": day.get("coldDays", 0),

        # RTE
        "rte": day.get("rteConsommation", 55000),
        "rteConsommation": day.get("rteConsommation", 55000),

        # Calendrier
        "weekday": weekday,
        "month": d.month,
        "day_of_month": d.day,
        "horizon": day.get("horizon", 0),
        "seasonDayIndex": season_day_index,
        "isWinter": int(is_winter(d)),
        "isWeekend": int(weekday >= 5),
        "winter_intensity": get_winter_intensity(d.month),

        # Tempo
        "remainingBleu": remaining_bleu,
        "remainingBlanc": remaining_blanc,
        "remainingRouge": remaining_rouge,
        "winterBleuRemaining": remaining_bleu if is_winter(d) else 0,
        "quota_pressure": quota_pressure
    }

    # ======================
    # BUILD X SELON FEATURES DU MODÈLE
    # ======================
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
    # 🔥 BOOST HIVERNAL (POST-ML)
    # En hiver, on augmente blanc/rouge si le ML est trop confiant sur bleu
    # ======================
    if is_winter(d) and weekday not in [5, 6]:  # Pas le weekend
        bleu_prob = ml_probs["bleu"]
        
        # Si ML prédit bleu avec forte confiance en hiver semaine → suspicious
        if bleu_prob > 0.5:
            # Réduire bleu, augmenter blanc/rouge proportionnellement
            reduction = (bleu_prob - 0.4) * 0.5  # Réduction progressive
            ml_probs["bleu"] = max(0.2, bleu_prob - reduction)
            
            # Redistribuer vers blanc/rouge
            if is_peak_winter(d):
                # Janvier/Février : plus de rouge probable
                ml_probs["blanc"] += reduction * 0.4
                ml_probs["rouge"] += reduction * 0.6
            else:
                # Nov/Dec/Mars : plus de blanc
                ml_probs["blanc"] += reduction * 0.6
                ml_probs["rouge"] += reduction * 0.4
        
        # Boost température froide
        if temp < 0:
            ml_probs["rouge"] = min(0.7, ml_probs["rouge"] * 1.5)
            ml_probs["bleu"] *= 0.7
        elif temp < 5:
            ml_probs["blanc"] = min(0.6, ml_probs["blanc"] * 1.3)
            ml_probs["bleu"] *= 0.85

    # ======================
    # 🔒 RÈGLES EDF ABSOLUES (POST-ML)
    # ======================
    
    # Rouge interdit hors hiver
    if not red_allowed(d):
        ml_probs["rouge"] = 0

    # Samedi : JAMAIS rouge
    if weekday == 5:
        ml_probs["rouge"] = 0

    # Dimanche : TOUJOURS bleu
    if weekday == 6:
        ml_probs = {"bleu": 1.0, "blanc": 0.0, "rouge": 0.0}

    # ======================
    # NORMALISATION
    # ======================
    total = sum(ml_probs.values())
    if total > 0:
        for c in COLORS:
            ml_probs[c] /= total
    else:
        # Fallback selon saison
        if is_winter(d):
            ml_probs = {"bleu": 0.3, "blanc": 0.45, "rouge": 0.25}
        else:
            ml_probs = {"bleu": 0.7, "blanc": 0.25, "rouge": 0.05}

    # Pas de 100% sauf dimanche
    if weekday != 6 and max(ml_probs.values()) > 0.85:
        top_color = max(ml_probs, key=ml_probs.get)
        ml_probs[top_color] = 0.85
        # Redistribuer 15%
        others = [c for c in COLORS if c != top_color]
        for c in others:
            ml_probs[c] += 0.075

    ml_color = max(ml_probs, key=ml_probs.get)

    predictions.append({
        "date": day["date"],
        "mlPrediction": ml_color,
        "mlProbabilities": {c: round(ml_probs[c] * 100) for c in COLORS},
        "mlConfidence": round(ml_probs[ml_color] * 100)
    })

    # Avance quotas simulés
    used_days[ml_color].add(day["date"])

# ======================
# SAVE
# ======================
OUTPUT_PATH.parent.mkdir(exist_ok=True)
OUTPUT_PATH.write_text(json.dumps(predictions, indent=2), encoding="utf-8")

print(f"\n✅ {len(predictions)} prédictions ML générées")
print("\n📊 Résumé des prédictions :")
for color in COLORS:
    count = sum(1 for p in predictions if p["mlPrediction"] == color)
    print(f"   {color}: {count}")
