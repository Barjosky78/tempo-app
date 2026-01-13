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

print("🤖 Lancement prédictions ML Tempo (robuste & aligné modèle)")

# ======================
# LOAD MODEL
# ======================
if not MODEL_PATH.exists():
    raise SystemExit("❌ Modèle ML introuvable")

bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
le = bundle["label_encoder"]
FEATURES = bundle["features"]  # 🔑 SOURCE DE VÉRITÉ

print("🧠 Features attendues par le modèle :", FEATURES)

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
        print("⚠️ history.json invalide → quotas ignorés :", e)

# ======================
# UTILS
# ======================
def is_winter(d: date) -> bool:
    return d.month in (11, 12, 1, 2, 3)

def red_allowed(d: date) -> bool:
    return is_winter(d)

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
    remaining = {
        "bleu":  max(0, MAX_DAYS["bleu"]  - len(used_days["bleu"])),
        "blanc": max(0, MAX_DAYS["blanc"] - len(used_days["blanc"])),
        "rouge": max(0, MAX_DAYS["rouge"] - len(used_days["rouge"]))
    }

    season_day_index = (d - SEASON_START).days + 1

    # ======================
    # FEATURE POOL COMPLET
    # (on fournit PLUS que nécessaire, puis on filtre)
    # ======================
    feature_pool = {
        # météo
        "temp": day.get("temperature", 8),
        "temperature": day.get("temperature", 8),
        "coldDays": day.get("coldDays", 0),

        # RTE
        "rte": day.get("rteConsommation", 55000),
        "rteConsommation": day.get("rteConsommation", 55000),

        # calendrier
        "weekday": weekday,
        "month": d.month,
        "horizon": day.get("horizon", 0),
        "seasonDayIndex": season_day_index,
        "isWinter": int(is_winter(d)),

        # Tempo
        "remainingBleu": remaining["bleu"],
        "remainingBlanc": remaining["blanc"],
        "remainingRouge": remaining["rouge"],
        "winterBleuRemaining": remaining["bleu"] if is_winter(d) else 0,
        "remainingTempoDays": remaining["bleu"] + remaining["blanc"] + remaining["rouge"]
    }

    # ======================
    # BUILD X STRICTEMENT SELON LE MODÈLE
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
    # 🔒 RÈGLES EDF (APRÈS ML)
    # ======================
    if not red_allowed(d):
        ml_probs["rouge"] = 0

    if weekday == 5:  # samedi
        ml_probs["rouge"] = 0

    if weekday == 6:  # dimanche
        ml_probs = {"bleu": 1.0, "blanc": 0.0, "rouge": 0.0}

    # ======================
    # NORMALISATION SAFE
    # ======================
    total = sum(ml_probs.values())
    if total > 0:
        for c in COLORS:
            ml_probs[c] /= total
    else:
        ml_probs = {"bleu": 0.6, "blanc": 0.3, "rouge": 0.1}

    ml_color = max(ml_probs, key=ml_probs.get)

    predictions.append({
        "date": day["date"],
        "mlPrediction": ml_color,
        "mlProbabilities": {c: round(ml_probs[c] * 100) for c in COLORS},
        "mlConfidence": round(ml_probs[ml_color] * 100)
    })

    # avance quotas simulés
    used_days[ml_color].add(day["date"])

# ======================
# SAVE
# ======================
OUTPUT_PATH.parent.mkdir(exist_ok=True)
OUTPUT_PATH.write_text(json.dumps(predictions, indent=2), encoding="utf-8")

print(f"✅ {len(predictions)} prédictions ML générées correctement")
