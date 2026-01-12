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
OUTPUT_PATH = BASE_DIR / "ML" / "ml_predictions.json"

print("🤖 Lancement prédictions ML (avec règles Tempo)")

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

predictions = []

# ======================
# PREDICT + RULES
# ======================
for day in tempo:

    # ❌ Pas de ML sur jour réel
    if day.get("fixed"):
        continue

    try:
        d = datetime.fromisoformat(day["date"])
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

    # ======================
    # 🔒 RÈGLES TEMPO EDF
    # ======================

    # ❌ ROUGE INTERDIT SAMEDI & DIMANCHE
    if weekday in (5, 6):
        ml_probs["rouge"] = 0
        corrected = True

    # 🔵 DIMANCHE = BLEU 100 %
    if weekday == 6:
        ml_probs["bleu"] = 100
        ml_probs["blanc"] = 0
        corrected = True

    # ======================
    # NORMALISATION APRÈS RÈGLES
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
        "correctedByRules": corrected
    })

# ======================
# SAVE
# ======================
OUTPUT_PATH.parent.mkdir(exist_ok=True)

with open(OUTPUT_PATH, "w") as f:
    json.dump(predictions, f, indent=2)

print(f"✅ {len(predictions)} prédictions ML générées avec règles Tempo")
