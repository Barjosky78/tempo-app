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

print("🤖 Lancement prédictions ML")

# ======================
# LOAD MODEL BUNDLE
# ======================
if not MODEL_PATH.exists():
    print("❌ Modèle ML introuvable")
    exit(1)

bundle = joblib.load(MODEL_PATH)

model = bundle["model"]
le = bundle["label_encoder"]
FEATURES = bundle["features"]

print("🧠 Modèle ML chargé")
print("🧩 Features utilisées :", FEATURES)

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
# PREDICT
# ======================
for day in tempo:
    if day.get("fixed"):
        continue  # pas de ML sur aujourd’hui réel

    try:
        d = datetime.fromisoformat(day["date"])
    except Exception:
        continue

    # === FEATURES STRICTEMENT IDENTIQUES AU TRAIN ===
    features = {
        "temp": day.get("temperature", 8),
        "coldDays": day.get("coldDays", 0),
        "rte": day.get("rteConsommation", 55000),
        "weekday": d.weekday(),
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

    ml_color = max(ml_probs, key=ml_probs.get)
    ml_confidence = ml_probs[ml_color]

    predictions.append({
        "date": day["date"],
        "mlPrediction": ml_color,
        "mlProbabilities": ml_probs,
        "mlConfidence": ml_confidence
    })

# ======================
# SAVE
# ======================
OUTPUT_PATH.parent.mkdir(exist_ok=True)

with open(OUTPUT_PATH, "w") as f:
    json.dump(predictions, f, indent=2)

print(f"✅ {len(predictions)} prédictions ML générées")
print("📁 Fichier :", OUTPUT_PATH)
