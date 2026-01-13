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

print("🤖 Lancement prédictions ML Tempo (modèle + règles EDF)")

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
if not MODEL_PATH.exists():
    raise SystemExit("❌ Modèle ML introuvable")

bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
le = bundle["label_encoder"]
FEATURES = bundle["features"]

# ======================
# LOAD DATA
# ======================
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
        print("⚠️ history.json invalide :", e)

# ======================
# UTILS
# ======================
def red_allowed(d: date) -> bool:
    return d.month in (11, 12, 1, 2, 3)

def in_winter(d: date) -> bool:
    return d.month in (11, 12, 1, 2, 3)

today = date.today()
season_year = today.year if today.month >= 9 else today.year - 1
SEASON_START = date(season_year, 9, 1)

# ======================
# PREDICTIONS
# ======================
predictions = []

for day in tempo:

    # Pas de ML sur jours EDF confirmés
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
    remaining_blanc = max(0, MAX_DAYS["blanc"] - len(used_days["blanc"]))
    remaining_rouge = max(0, MAX_DAYS["rouge"] - len(used_days["rouge"]))

    # 🔑 BLEU RESTANT **EN HIVER SEULEMENT**
    winter_bleu_remaining = (
        max(0, MAX_DAYS["bleu"] - len(used_days["bleu"]))
        if in_winter(d)
        else 0
    )

    season_day_index = (d - SEASON_START).days + 1

    # ======================
    # FEATURES ML (STRICTEMENT IDENTIQUES AU TRAIN)
    # ======================
    X = pd.DataFrame([{
        "temp": day.get("temperature", 8),
        "coldDays": day.get("coldDays", 0),
        "rte": day.get("rteConsommation", 55000),
        "weekday": weekday,
        "month": d.month,
        "horizon": day.get("horizon", 0),

        "remainingBlanc": remaining_blanc,
        "remainingRouge": remaining_rouge,
        "winterBleuRemaining": winter_bleu_remaining,
        "seasonDayIndex": season_day_index
    }])

    # Sécurité ordre features
    X = X[FEATURES]

    probs = model.predict_proba(X)[0]
    classes = le.inverse_transform(range(len(probs)))

    ml_probs = {c: 0.0 for c in COLORS}
    for i, c in enumerate(classes):
        ml_probs[c] = float(probs[i])

    corrected = False
    rules = []

    # ======================
    # 🔒 RÈGLES EDF STRICTES
    # ======================
    if not red_allowed(d):
        ml_probs["rouge"] = 0
        rules.append("rouge_hors_periode")
        corrected = True

    if weekday == 5:  # samedi
        ml_probs["rouge"] = 0
        rules.append("samedi_pas_rouge")
        corrected = True

    if weekday == 6:  # dimanche
        ml_probs = {"bleu": 1.0, "blanc": 0.0, "rouge": 0.0}
        rules.append("dimanche_bleu_force")
        corrected = True

    # ======================
    # 🧮 QUOTAS
    # ======================
    if remaining_blanc <= 0:
        ml_probs["blanc"] = 0
        rules.append("quota_blanc_epuise")
        corrected = True

    if remaining_rouge <= 0:
        ml_probs["rouge"] = 0
        rules.append("quota_rouge_epuise")
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

    # Anti 100 %
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
        "remainingDays": {
            "blanc": remaining_blanc,
            "rouge": remaining_rouge,
            "winterBleu": winter_bleu_remaining
        }
    })

    # Avance quotas simulés
    used_days[ml_color].add(day["date"])

# ======================
# SAVE
# ======================
OUTPUT_PATH.parent.mkdir(exist_ok=True)
OUTPUT_PATH.write_text(json.dumps(predictions, indent=2), encoding="utf-8")

print(f"✅ {len(predictions)} prédictions ML générées (logique Tempo saine)")
