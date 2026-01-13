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

print("🤖 Lancement prédictions ML (Tempo + quotas + règles EDF)")

# ======================
# CONSTANTES TEMPO
# ======================
MAX_DAYS = {
    "bleu": 300,
    "blanc": 43,
    "rouge": 22
}

COLORS = ["bleu", "blanc", "rouge"]

# ======================
# LOAD MODEL
# ======================
if not MODEL_PATH.exists():
    raise SystemExit("❌ Modèle ML introuvable")

bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
le = bundle["label_encoder"]

# ======================
# LOAD TEMPO
# ======================
with open(TEMPO_PATH, "r", encoding="utf-8") as f:
    tempo = json.load(f)

# ======================
# LOAD HISTORY (QUOTAS RÉELS)
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
        print("⚠️ history.json invalide → quotas ignorés", e)

# ======================
# SAISON TEMPO
# ======================
today = date.today()
season_year = today.year if today.month >= 9 else today.year - 1
SEASON_START = date(season_year, 9, 1)

def red_allowed(d: date) -> bool:
    return d.month in (11, 12, 1, 2, 3)

# ======================
# PREDICTIONS
# ======================
predictions = []

for day in tempo:

    # Pas de ML sur jours EDF officiels
    if day.get("fixed"):
        continue

    try:
        d = datetime.fromisoformat(day["date"]).date()
    except Exception:
        continue

    weekday = d.weekday()  # 0=lundi … 6=dimanche

    # ======================
    # QUOTAS RESTANTS
    # ======================
    remaining = {
        c: max(0, MAX_DAYS[c] - len(used_days[c]))
        for c in COLORS
    }

    season_day_index = (d - SEASON_START).days + 1

    # ======================
    # FEATURES ML (IDENTIQUES AU TRAIN)
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

    # ⚠️ PAS de round ici
    ml_probs = {c: 0.0 for c in COLORS}
    for i, c in enumerate(classes):
        ml_probs[c] = float(probs[i])

    corrected = False
    rule_details = []

    # ======================
    # BOOST BLANC J1 / J2 EN HIVER
    # ======================
    if d.month in (11, 12, 1, 2, 3) and day.get("horizon", 0) in (1, 2):
        ml_probs["blanc"] += 0.08
        corrected = True
        rule_details.append("boost_blanc_hiver_J1_J2")

    # ======================
    # RÈGLES EDF
    # ======================
    if not red_allowed(d):
        ml_probs["rouge"] = 0
        corrected = True
        rule_details.append("rouge_hors_periode")

    if weekday == 6:  # dimanche
        ml_probs = {"bleu": 1.0, "blanc": 0.0, "rouge": 0.0}
        corrected = True
        rule_details.append("dimanche_bleu_force")

    # ======================
    # QUOTAS
    # ======================
    for c in COLORS:
        if remaining[c] <= 0:
            ml_probs[c] = 0
            corrected = True
            rule_details.append(f"quota_{c}_epuise")

    # ======================
    # NORMALISATION (SAFE)
    # ======================
    total = sum(ml_probs.values())

    if total <= 0:
        ml_probs = {"bleu": 0.6, "blanc": 0.3, "rouge": 0.1}
        rule_details.append("fallback_soft")
    else:
        for c in COLORS:
            ml_probs[c] /= total

    # ❌ Interdiction du 100% hors EDF
    if max(ml_probs.values()) > 0.95:
        ml_probs = {"bleu": 0.7, "blanc": 0.25, "rouge": 0.05}
        rule_details.append("anti_100_percent")

    # ======================
    # FINAL
    # ======================
    ml_color = max(ml_probs, key=ml_probs.get)

    predictions.append({
        "date": day["date"],
        "mlPrediction": ml_color,
        "mlProbabilities": {
            c: round(ml_probs[c] * 100)
            for c in COLORS
        },
        "mlConfidence": round(ml_probs[ml_color] * 100),
        "correctedByRules": corrected,
        "ruleDetails": rule_details,
        "remainingDays": remaining
    })

    # avance les quotas simulés
    used_days[ml_color].add(day["date"])

# ======================
# SAVE
# ======================
OUTPUT_PATH.parent.mkdir(exist_ok=True)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(predictions, f, indent=2)

print(f"✅ {len(predictions)} prédictions ML générées")
