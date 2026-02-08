"""
🌲 Entraînement ML Tempo - CORRIGÉ
GradientBoosting avec les 3 couleurs (bleu, blanc, rouge)
et poids de classe adaptés à la saisonnalité.
"""
import json
import pandas as pd
import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score
from pathlib import Path
from collections import Counter

# ======================
# PATHS
# ======================
DATASET_PATH = Path("ML/ml_dataset.json")
MODEL_PATH   = Path("ML/ml_model.pkl")

print("🌲 Entraînement ML Tempo (GradientBoosting - 3 couleurs)")

# ======================
# LOAD DATASET
# ======================
if not DATASET_PATH.exists():
    raise SystemExit("❌ Dataset ML introuvable")

df = pd.read_json(DATASET_PATH)

print(f"📊 Échantillons disponibles : {len(df)}")

if len(df) < 200:
    raise SystemExit("❌ Dataset insuffisant pour entraîner un modèle fiable")

# ======================
# ANALYSE DISTRIBUTION
# ======================
color_counts = df["color"].value_counts()
print("\n📈 Distribution des couleurs :")
for color, count in color_counts.items():
    pct = count / len(df) * 100
    print(f"   {color}: {count} ({pct:.1f}%)")

# Vérification critique
if "bleu" not in color_counts.index:
    raise SystemExit("❌ ERREUR : Pas de jours bleu dans le dataset ! "
                     "Exécutez build_history_from_tempo_api.py d'abord.")

# Distribution par mois hivernal
print("\n📅 Distribution par mois hivernal :")
df["_month"] = pd.to_datetime(df["date"]).dt.month
for month in [11, 12, 1, 2, 3]:
    month_df = df[df["_month"] == month]
    if len(month_df) > 0:
        dist = month_df["color"].value_counts(normalize=True) * 100
        print(f"   Mois {month:02d}: "
              f"bleu={dist.get('bleu', 0):.0f}% "
              f"blanc={dist.get('blanc', 0):.0f}% "
              f"rouge={dist.get('rouge', 0):.0f}%")

# ======================
# FEATURE ENGINEERING
# ======================
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

df["weekday"] = df["date"].dt.weekday
df["month"]   = df["date"].dt.month
df["day_of_month"] = df["date"].dt.day

if "temperature" in df.columns and "temp" not in df.columns:
    df["temp"] = df["temperature"]
if "rteConsommation" in df.columns and "rte" not in df.columns:
    df["rte"] = df["rteConsommation"]

if "horizon" not in df.columns:
    df["horizon"] = 0
if "winterBleuRemaining" not in df.columns:
    df["winterBleuRemaining"] = df.get("remainingBleu", pd.Series([300]*len(df)))
if "isWinter" not in df.columns:
    df["isWinter"] = df["month"].isin([11, 12, 1, 2, 3]).astype(int)
if "isWeekend" not in df.columns:
    df["isWeekend"] = df["weekday"].isin([5, 6]).astype(int)

# Catégorie de température
df["temp_cat"] = pd.cut(
    df["temp"].fillna(10), 
    bins=[-50, -5, 0, 5, 10, 15, 50],
    labels=[0, 1, 2, 3, 4, 5]
).astype(int)

# Intensité hivernale
df["winter_intensity"] = df["month"].map({
    11: 2, 12: 3, 1: 4, 2: 4, 3: 2
}).fillna(0).astype(int)

# Pression quotas
if "remainingBlanc" in df.columns and "remainingRouge" in df.columns:
    df["quota_pressure"] = (
        (43 - df["remainingBlanc"]) / 43 * 0.5 +
        (22 - df["remainingRouge"]) / 22 * 0.5
    ).clip(0, 1)
else:
    df["quota_pressure"] = 0.0

# ======================
# FEATURES OPTIMISÉES
# ======================
FEATURES = [
    "temp", "temp_cat", "coldDays",
    "rte",
    "weekday", "month", "day_of_month",
    "isWeekend", "isWinter", "winter_intensity",
    "remainingBlanc", "remainingRouge", "winterBleuRemaining",
    "seasonDayIndex", "quota_pressure",
    "horizon"
]

available_features = [f for f in FEATURES if f in df.columns]
missing = [f for f in FEATURES if f not in df.columns]
if missing:
    print(f"⚠️ Features manquantes : {missing}")

FEATURES = available_features
print(f"\n✅ Features utilisées ({len(FEATURES)}) : {FEATURES}")

df[FEATURES] = df[FEATURES].fillna(0)
X = df[FEATURES]
y = df["color"]

# ======================
# LABEL ENCODER
# ======================
le = LabelEncoder()
y_enc = le.fit_transform(y)
classes = list(le.classes_)
print(f"🏷️ Classes : {classes}")

# ======================
# CLASS WEIGHTS
# ======================
freq = Counter(y)
total = sum(freq.values())

# Poids inversement proportionnels à la fréquence
# Blanc/rouge sont rares mais CRITIQUES à bien prédire
BASE_WEIGHTS = {}
for c in classes:
    base_w = total / (len(classes) * freq.get(c, 1))
    # Bonus pour blanc et rouge (plus important à détecter)
    if c == "rouge":
        BASE_WEIGHTS[c] = max(base_w * 1.5, 3.0)
    elif c == "blanc":
        BASE_WEIGHTS[c] = max(base_w * 1.3, 2.0)
    else:
        BASE_WEIGHTS[c] = max(base_w, 1.0)

print(f"⚖️ Poids : {BASE_WEIGHTS}")

sample_weights = [BASE_WEIGHTS[label] for label in y]

# ======================
# TRAIN GRADIENT BOOSTING
# ======================
print("\n🚀 Entraînement GradientBoosting...")

model = GradientBoostingClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.08,
    min_samples_leaf=8,
    subsample=0.85,
    random_state=42
)

model.fit(X, y_enc, sample_weight=sample_weights)

# ======================
# VALIDATION
# ======================
print("\n📊 Validation croisée (5-fold)...")
scores = cross_val_score(model, X, y_enc, cv=5, scoring='accuracy')
print(f"   Accuracy : {scores.mean():.2%} (+/- {scores.std()*2:.2%})")

# Validation par couleur
from sklearn.metrics import classification_report
y_pred = model.predict(X)
y_pred_labels = le.inverse_transform(y_pred)
print("\n📊 Rapport par couleur (sur données d'entraînement) :")
print(classification_report(y, y_pred_labels, zero_division=0))

# ======================
# FEATURE IMPORTANCE
# ======================
print("🔍 Importance des features :")
importances = sorted(
    zip(FEATURES, model.feature_importances_),
    key=lambda x: x[1], reverse=True
)
for feat, imp in importances[:10]:
    print(f"   {feat}: {imp:.3f}")

# ======================
# SAVE
# ======================
bundle = {
    "model": model,
    "label_encoder": le,
    "features": FEATURES,
    "class_weights": BASE_WEIGHTS,
    "model_type": "GradientBoosting",
    "classes": classes,
    "training_samples": len(df),
    "training_accuracy": float(scores.mean())
}

MODEL_PATH.parent.mkdir(exist_ok=True)
joblib.dump(bundle, MODEL_PATH)

size = MODEL_PATH.stat().st_size
print(f"\n✅ Modèle sauvegardé ({size:,} bytes)")
print(f"🎉 Entraîné sur {len(df)} échantillons avec 3 couleurs !")
