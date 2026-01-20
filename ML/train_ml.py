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

print("🌲 Entraînement ML Tempo OPTIMISÉ (GradientBoosting + boost hivernal)")

# ======================
# LOAD DATASET
# ======================
if not DATASET_PATH.exists():
    raise SystemExit("❌ Dataset ML introuvable")

df = pd.read_json(DATASET_PATH)

print(f"📊 Échantillons disponibles : {len(df)}")
print("🧱 Colonnes dataset :", list(df.columns))

if len(df) < 200:
    raise SystemExit("❌ Dataset insuffisant pour entraîner un modèle fiable")

# ======================
# ANALYSE DISTRIBUTION
# ======================
color_counts = df["color"].value_counts()
print("\n📈 Distribution des couleurs dans le dataset :")
for color, count in color_counts.items():
    pct = count / len(df) * 100
    print(f"   {color}: {count} ({pct:.1f}%)")

# Distribution par mois
print("\n📅 Distribution par mois (hiver = nov-mars) :")
df["_month"] = pd.to_datetime(df["date"]).dt.month
for month in [11, 12, 1, 2, 3]:
    month_df = df[df["_month"] == month]
    if len(month_df) > 0:
        month_dist = month_df["color"].value_counts(normalize=True) * 100
        print(f"   Mois {month:02d}: bleu={month_dist.get('bleu', 0):.0f}% blanc={month_dist.get('blanc', 0):.0f}% rouge={month_dist.get('rouge', 0):.0f}%")

# ======================
# FEATURE ENGINEERING
# ======================
print("\n🛠️ Construction des features")

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

# Features temporelles de base
df["weekday"] = df["date"].dt.weekday
df["month"]   = df["date"].dt.month
df["day_of_month"] = df["date"].dt.day

# Harmonisation des noms (compatibilité)
if "temperature" in df.columns and "temp" not in df.columns:
    df["temp"] = df["temperature"]
if "rteConsommation" in df.columns and "rte" not in df.columns:
    df["rte"] = df["rteConsommation"]

# Features supplémentaires si manquantes
if "horizon" not in df.columns:
    df["horizon"] = 0

if "winterBleuRemaining" not in df.columns:
    df["winterBleuRemaining"] = df.get("remainingBleu", 300)

if "isWinter" not in df.columns:
    df["isWinter"] = df["month"].isin([11, 12, 1, 2, 3]).astype(int)

if "isWeekend" not in df.columns:
    df["isWeekend"] = df["weekday"].isin([5, 6]).astype(int)

# 🔑 NOUVELLES FEATURES OPTIMISÉES
# Catégorie de température (crucial pour prédiction)
df["temp_cat"] = pd.cut(
    df["temp"], 
    bins=[-50, -5, 0, 5, 10, 15, 50],
    labels=[0, 1, 2, 3, 4, 5]  # 0=très froid, 5=doux
).astype(int)

# Mois hivernal pondéré (janvier/février = pic)
df["winter_intensity"] = df["month"].map({
    11: 2,  # Novembre - début hiver
    12: 3,  # Décembre - hiver
    1: 4,   # Janvier - pic hiver
    2: 4,   # Février - pic hiver  
    3: 2,   # Mars - fin hiver
}).fillna(0).astype(int)

# Stress de fin de saison (quotas à écouler)
df["quota_pressure"] = (
    (43 - df.get("remainingBlanc", 43)) / 43 * 0.5 +
    (22 - df.get("remainingRouge", 22)) / 22 * 0.5
).clip(0, 1)

# ======================
# TARGET
# ======================
df["label"] = df["color"]

# ======================
# FEATURES OPTIMISÉES
# ======================
FEATURES = [
    # Météo (CRUCIAL)
    "temp",
    "temp_cat",
    "coldDays",
    
    # Énergie
    "rte",
    
    # Calendrier
    "weekday",
    "month",
    "day_of_month",
    "isWeekend",
    "isWinter",
    "winter_intensity",
    
    # Contexte Tempo
    "remainingBlanc",
    "remainingRouge",
    "winterBleuRemaining",
    "seasonDayIndex",
    "quota_pressure",
    
    # Horizon prédiction
    "horizon"
]

TARGET = "label"

# Vérification colonnes
available_features = [f for f in FEATURES if f in df.columns]
missing_features = [f for f in FEATURES if f not in df.columns]

if missing_features:
    print(f"⚠️ Features manquantes (ignorées) : {missing_features}")

FEATURES = available_features
print(f"✅ Features utilisées : {FEATURES}")

df[FEATURES] = df[FEATURES].fillna(0)

X = df[FEATURES]
y = df[TARGET]

# ======================
# LABEL ENCODER
# ======================
le = LabelEncoder()
y_enc = le.fit_transform(y)

classes = list(le.classes_)
print(f"\n🏷️ Classes apprises : {classes}")

# ======================
# CLASS WEIGHTS OPTIMISÉS POUR L'HIVER
# ======================
# En hiver, bleu est RARE (surtout semaine)
# On pénalise fortement les erreurs sur blanc/rouge

# Calculer les poids inverses à la fréquence
freq = Counter(y)
total = sum(freq.values())

# Poids de base inversement proportionnels à la fréquence
# + boost manuel pour blanc/rouge car plus importants à prédire
BASE_WEIGHTS = {
    "bleu": 1.0,
    "blanc": max(4.0, total / (3 * freq.get("blanc", 1))),  # Min 4x
    "rouge": max(8.0, total / (3 * freq.get("rouge", 1)))   # Min 8x
}

class_weight = {
    le.transform([c])[0]: BASE_WEIGHTS[c]
    for c in classes
}

print(f"⚖️ Poids calculés : {BASE_WEIGHTS}")

# ======================
# TRAIN GRADIENT BOOSTING (meilleur que RandomForest pour ce cas)
# ======================
print("\n🚀 Entraînement GradientBoosting")

model = GradientBoostingClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.1,
    min_samples_leaf=10,
    subsample=0.8,
    random_state=42
)

# Note: GradientBoosting n'a pas de class_weight natif
# On utilise sample_weight à la place
sample_weights = [BASE_WEIGHTS[label] for label in y]

model.fit(X, y_enc, sample_weight=sample_weights)

# ======================
# VALIDATION CROISÉE
# ======================
print("\n📊 Validation croisée (5-fold)...")
scores = cross_val_score(model, X, y_enc, cv=5, scoring='accuracy')
print(f"   Accuracy moyenne : {scores.mean():.2%} (+/- {scores.std()*2:.2%})")

# ======================
# FEATURE IMPORTANCE
# ======================
print("\n🔍 Importance des features :")
importances = sorted(
    zip(FEATURES, model.feature_importances_),
    key=lambda x: x[1],
    reverse=True
)
for feat, imp in importances[:10]:
    print(f"   {feat}: {imp:.3f}")

# ======================
# SAVE MODEL
# ======================
bundle = {
    "model": model,
    "label_encoder": le,
    "features": FEATURES,
    "class_weights": BASE_WEIGHTS,
    "model_type": "GradientBoosting"
}

MODEL_PATH.parent.mkdir(exist_ok=True)
joblib.dump(bundle, MODEL_PATH)

size = MODEL_PATH.stat().st_size

print(f"\n✅ Modèle GradientBoosting entraîné")
print(f"📦 Taille du modèle : {size:,} bytes")

if size < 10_000:
    raise SystemExit("❌ Modèle anormalement petit")

print("\n🎉 ML optimisé — Blanc/Rouge mieux pondérés pour l'hiver !")
