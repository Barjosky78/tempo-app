import json
import pandas as pd
import joblib
from datetime import datetime
from pathlib import Path

# ======================
# PATHS
# ======================
BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = BASE_DIR / "ML" / "ml_model.pkl"
TEMPO_PATH = BASE_DIR / "tempo.json"
HISTORY_PATH = BASE_DIR / "history.json"
OUTPUT_PATH = BASE_DIR / "ML" / "ml_predictions.json"

print("🤖 Lancement prédictions ML (règles Tempo + quotas)")

# ======================
# CONSTANTES TEMPO
# ======================
MAX_DAYS = {
    "bleu": 300,
    "blanc": 43,
    "rouge": 22
}

# ======================
# LOAD MODEL
# ======================
if not MODEL_PATH.exists():
    print("❌ Modèle ML introuvable")
    exit(1)

bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
le = bundle["label_encoder"]
FEATURES = bundle["features"]

# ======================
# LOAD TEMPO
# ======================
if not TEMPO_PATH.exists():
    print("❌ tempo.json introuvable")
    exit(1)

with open(TEMPO_PATH, "r") as f:
    tempo = json.load(f)

# ======================
# LOAD HISTORY (pour quotas)
# ======================
used_days = {
    "bleu": set(),
    "blanc": set(),
    "rouge": set()
}

if HISTORY_PATH.exists():
    with open(HISTORY_PATH, "r") as f:
        history = json.load(f)

    for h in history:
        if h.get("realColor"):
            used_days[h["realColor"]].add(h["date"])

# ======================
# SAISON TEMPO
# ======================
today = datetime.now().date()
season_year = today.year if today.month >= 11 else today.year - 1

SEASON_START = datetime(season_year, 11, 1).date()
SEASON_END   = datetime(season_year + 1, 3, 31).date()

def in_season(d):
    return SEASON_START <= d <= SEASON_END

# ======================
# PREDICT + RÈGLES
# ======================
predictions = []

for day in tempo:

    # ❌ Pas de ML sur jours EDF réels
    if day.get("fixed"):
        continue

    try:
        d = datetime.fromisoformat(day["date"]).date()
    except Exception:
        continue

    weekday = d.weekday()  # 0=lundi ... 5=samedi 6=dimanche

    # ======================
    # FEATURES (identiques au train)
    # ======================
    features = {
        "temp": day.get("temperature", 8),
        "coldDays": day.get("coldDays", 0),
        "rte": day.get("rteConsommation", 55000),
        "weekday": weekday,
        "month": d.month,
        "horizon": day.get("horizon", 0),
    }

    X = pd.DataFrame([features])
    probs = model.predict_proba(X)[0]
    classes = le.inverse_transform(range(len(probs)))

    ml_probs = {
        classes[i]: round(probs[i] * 100)
        for i in range(len(classes))
    }

    corrected = False
    corrections = []

    # ======================
    # 🔒 RÈGLES TEMPO EDF
    # ======================

    # ❌ ROUGE HORS SAISON
    if not in_season(d):
        if ml_probs.get("rouge", 0) > 0:
            ml_probs["rouge"] = 0
            corrected = True
            corrections.append("rouge_hors_saison")

    # ❌ ROUGE INTERDIT SAMEDI / DIMANCHE
    if weekday in (5, 6):
        if ml_probs.get("rouge", 0) > 0:
            ml_probs["rouge"] = 0
            corrected = True
            corrections.append("rouge_weekend")

    # 🔵 DIMANCHE = BLEU FORCÉ
    if weekday == 6:
        ml_probs["bleu"] = 100
        ml_probs["blanc"] = 0
        ml_probs["rouge"] = 0
        corrected = True
        corrections.append("dimanche_bleu")

    # ======================
    # 🧮 QUOTAS RESTANTS
    # ======================
    remaining = {
        k: MAX_DAYS[k] - len(used_days[k])
        for k in MAX_DAYS
    }

    for color, rest in remaining.items():
        if rest <= 0 and ml_probs.get(color, 0) > 0:
            ml_probs[color] = 0
            corrected = True
            corrections.append(f"quota_{color}_epuise")

    # ======================
    # NORMALISATION
    # ======================
    total = sum(ml_probs.values())

    if total > 0:
        for k in ml_probs:
            ml_probs[k] = round(ml_probs[k] / total * 100)

    # Sécurité somme = 100
    diff = 100 - sum(ml_probs.values())
    if diff != 0:
        best = max(ml_probs, key=ml_probs.get)
        ml_probs[best] += diff

    ml_color = max(ml_probs, key=ml_probs.get)
    ml_confidence = ml_probs[ml_color]

    predictions.append({
        "date": day["date"],
        "mlPrediction": ml_color,
        "mlProbabilities": ml_probs,
        "mlConfidence": ml_confidence,
        "correctedByRules": corrected,
        "ruleDetails": corrections,
        "remainingDays": remaining
    })

# ======================
# SAVE
# ======================
OUTPUT_PATH.parent.mkdir(exist_ok=True)

with open(OUTPUT_PATH, "w") as f:
    json.dump(predictions, f, indent=2)

print(f"✅ {len(predictions)} prédictions ML générées (règles + quotas intégrés)")
