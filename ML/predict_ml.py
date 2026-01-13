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

print("🤖 Lancement prédictions ML (Tempo + règles EDF + biais métier)")

# ======================
# CONSTANTES
# ======================
COLORS = ["bleu", "blanc", "rouge"]

MAX_DAYS = {
    "bleu": 300,
    "blanc": 43,
    "rouge": 22
}

# ======================
# LOAD MODEL
# ======================
bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
le = bundle["label_encoder"]

# ======================
# LOAD DATA
# ======================
tempo = json.loads(TEMPO_PATH.read_text(encoding="utf-8"))

used_days = {c: set() for c in COLORS}
if HISTORY_PATH.exists():
    try:
        history = json.loads(HISTORY_PATH.read_text(encoding="utf-8") or "[]")
        for h in history:
            if h.get("realColor") in used_days:
                used_days[h["realColor"]].add(h["date"])
    except Exception as e:
        print("⚠️ history.json invalide :", e)

# ======================
# UTILS
# ======================
def red_allowed(d: date) -> bool:
    return d.month in (11, 12, 1, 2, 3)

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

    # ======================
    # QUOTAS RESTANTS
    # ======================
    remaining = {
        c: max(0, MAX_DAYS[c] - len(used_days[c]))
        for c in COLORS
    }

    season_day_index = (d - SEASON_START).days + 1

    # ======================
    # FEATURES ML
    # ======================
    X = pd.DataFrame([{
        "temp": day.get("temperature", 8),
        "coldDays": day.get("coldDays", 0),
        "rte": day.get("rteConsommation", 55000),
        "weekday": weekday,
        "month": d.month,
        "horizon": day.get("horizon", 0),
        "remainingBleu": remaining["bleu"],
        "remainingBlanc": remaining["blanc"],
        "remainingRouge": remaining["rouge"],
        "seasonDayIndex": season_day_index
    }])

    probs = model.predict_proba(X)[0]
    classes = le.inverse_transform(range(len(probs)))

    ml_probs = {c: 0.0 for c in COLORS}
    for i, c in enumerate(classes):
        ml_probs[c] = float(probs[i])

    corrected = False
    rules = []

    # ======================
    # ❄️ BIAIS HIVER (CLÉ)
    # ======================
    if d.month in (11, 12, 1, 2, 3):
        ml_probs["bleu"] *= 0.65
        ml_probs["blanc"] *= 1.25
        ml_probs["rouge"] *= 1.15
        corrected = True
        rules.append("bias_hiver")

    # ======================
    # 📆 WEEK-END EDF
    # ======================
    if weekday == 5:  # samedi
        ml_probs["rouge"] = 0
        rules.append("samedi_pas_rouge")
        corrected = True

    if weekday == 6:  # dimanche
        ml_probs = {"bleu": 1.0, "blanc": 0.0, "rouge": 0.0}
        rules.append("dimanche_bleu_force")
        corrected = True

    # ======================
    # 🚫 ROUGE HORS PÉRIODE
    # ======================
    if not red_allowed(d):
        ml_probs["rouge"] = 0
        rules.append("rouge_hors_periode")
        corrected = True

    # ======================
    # 🧮 QUOTAS
    # ======================
    for c in COLORS:
        if remaining[c] <= 0:
            ml_probs[c] = 0
            rules.append(f"quota_{c}_epuise")
            corrected = True

    # ======================
    # 🔵 PLAFOND BLEU HIVER
    # ======================
    if d.month in (11, 12, 1, 2, 3) and ml_probs["bleu"] > 0.6:
        excess = ml_probs["bleu"] - 0.6
        ml_probs["bleu"] = 0.6
        ml_probs["blanc"] += excess * 0.6
        ml_probs["rouge"] += excess * 0.4
        rules.append("plafond_bleu_hiver")
        corrected = True

    # ======================
    # NORMALISATION
    # ======================
    total = sum(ml_probs.values())
    if total <= 0:
        ml_probs = {"bleu": 0.6, "blanc": 0.3, "rouge": 0.1}
        rules.append("fallback_soft")
    else:
        for c in COLORS:
            ml_probs[c] /= total

    # anti 100%
    if max(ml_probs.values()) > 0.95:
        ml_probs = {"bleu": 0.65, "blanc": 0.25, "rouge": 0.10}
        rules.append("anti_100")
        corrected = True

    ml_color = max(ml_probs, key=ml_probs.get)

    predictions.append({
        "date": day["date"],
        "mlPrediction": ml_color,
        "mlProbabilities": {c: round(ml_probs[c] * 100) for c in COLORS},
        "mlConfidence": round(ml_probs[ml_color] * 100),
        "correctedByRules": corrected,
        "ruleDetails": rules,
        "remainingDays": remaining
    })

    used_days[ml_color].add(day["date"])

# ======================
# SAVE
# ======================
OUTPUT_PATH.parent.mkdir(exist_ok=True)
OUTPUT_PATH.write_text(json.dumps(predictions, indent=2), encoding="utf-8")

print(f"✅ {len(predictions)} prédictions ML générées")
