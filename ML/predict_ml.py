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
if not TEMPO_PATH.exists():
    raise SystemExit("❌ tempo.json introuvable")

with open(TEMPO_PATH, "r", encoding="utf-8") as f:
    tempo = json.load(f)

# ======================
# LOAD HISTORY (QUOTAS)
# ======================
used_days = {
    "bleu": set(),
    "blanc": set(),
    "rouge": set()
}

if HISTORY_PATH.exists():
    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        history = json.load(f)

    for h in history:
        color = h.get("realColor")
        if color in used_days:
            used_days[color].add(h["date"])

# ======================
# SAISON TEMPO (1/09 → 31/08)
# ======================
today = date.today()
season_year = today.year if today.month >= 9 else today.year - 1

SEASON_START = date(season_year, 9, 1)
SEASON_END   = date(season_year + 1, 8, 31)

def in_tempo_season(d: date) -> bool:
    return SEASON_START <= d <= SEASON_END

def red_allowed(d: date) -> bool:
    return d.month in (11, 12, 1, 2, 3)

# ======================
# PREDICTIONS
# ======================
predictions = []

for day in tempo:

    # ❌ Pas de ML sur jours EDF confirmés
    if day.get("fixed"):
        continue

    try:
        d = datetime.fromisoformat(day["date"]).date()
    except Exception:
        continue

    weekday = d.weekday()  # 0=lundi ... 5=samedi 6=dimanche

    # ======================
    # FEATURES (IDENTIQUES AU TRAIN)
    # ======================
    X = pd.DataFrame([{
        "temp": day.get("temperature", 8),
        "coldDays": day.get("coldDays", 0),
        "rte": day.get("rteConsommation", 55000),
        "weekday": weekday,
        "month": d.month,
        "horizon": day.get("horizon", 0)
    }])

    probs = model.predict_proba(X)[0]
    classes = le.inverse_transform(range(len(probs)))

    ml_probs = {
        classes[i]: round(probs[i] * 100)
        for i in range(len(classes))
    }

    corrected = False
    rule_details = []

    # ======================
    # 🔒 RÈGLES TEMPO EDF
    # ======================

    # ❌ ROUGE HORS PÉRIODE HIVER
    if ml_probs.get("rouge", 0) > 0 and not red_allowed(d):
        ml_probs["rouge"] = 0
        corrected = True
        rule_details.append("rouge_hors_periode_1nov_31mars")

    # ❌ ROUGE INTERDIT WEEK-END
    if weekday in (5, 6) and ml_probs.get("rouge", 0) > 0:
        ml_probs["rouge"] = 0
        corrected = True
        rule_details.append("rouge_interdit_weekend")

    # 🔵 DIMANCHE = BLEU 100 %
    if weekday == 6:
        ml_probs = {"bleu": 100, "blanc": 0, "rouge": 0}
        corrected = True
        rule_details.append("dimanche_bleu_force")

    # ======================
    # 🧮 QUOTAS RESTANTS
    # ======================
    remaining = {
        c: max(0, MAX_DAYS[c] - len(used_days[c]))
        for c in MAX_DAYS
    }

    for color, rest in remaining.items():
        if rest <= 0 and ml_probs.get(color, 0) > 0:
            ml_probs[color] = 0
            corrected = True
            rule_details.append(f"quota_{color}_epuise")

    # ======================
    # NORMALISATION
    # ======================
    total = sum(ml_probs.values())

    if total == 0:
        ml_probs = {"bleu": 100, "blanc": 0, "rouge": 0}
        rule_details.append("fallback_bleu")
    else:
        for k in ml_probs:
            ml_probs[k] = round(ml_probs[k] / total * 100)

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
        "ruleDetails": rule_details,
        "remainingDays": remaining
    })

# ======================
# SAVE
# ======================
OUTPUT_PATH.parent.mkdir(exist_ok=True)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(predictions, f, indent=2)

print(f"✅ {len(predictions)} prédictions ML générées avec règles Tempo complètes")
