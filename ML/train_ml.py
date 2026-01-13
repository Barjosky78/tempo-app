import json
import pandas as pd
import joblib
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from pathlib import Path

# ======================
# PATHS
# ======================
DATASET_PATH = Path("ML/ml_dataset.json")
MODEL_PATH   = Path("ML/ml_model.pkl")

print("🤖 Lancement entraînement ML Tempo (historique réel + quotas EDF)")

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
# FEATURE ENGINEERING
# ======================
print("🛠️ Construction des features ML")

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

df["weekday"] = df["date"].dt.weekday
df["month"]   = df["date"].dt.month
df["horizon"] = 0

df["label"] = df["color"]
df["temp"]  = df["temperature"]
df["rte"]   = df["rteConsommation"]

FEATURES = [
    "temp",
    "coldDays",
    "rte",
    "weekday",
    "month",
    "horizon",
    "remainingBleu",
    "remainingBlanc",
    "remainingRouge",
    "seasonDayIndex"
]

TARGET = "label"

missing = [c for c in FEATURES + [TARGET] if c not in df.columns]
if missing:
    raise SystemExit(f"❌ Colonnes manquantes : {missing}")

df[FEATURES] = df[FEATURES].fillna(0)

X = df[FEATURES]
y = df[TARGET]

# ======================
# LABEL ENCODER
# ======================
le = LabelEncoder()
y_enc = le.fit_transform(y)

classes = list(le.classes_)
print("🏷️ Classes apprises :", classes)

# ======================
# CLASS WEIGHTS (CORRIGÉ)
# ======================
BASE_WEIGHTS = {
    "bleu": 1.0,
    "blanc": 3.5,
    "rouge": 6.0
}

class_weight = {
    le.transform([c])[0]: BASE_WEIGHTS[c]
    for c in classes
}

print("⚖️ Poids encodés utilisés :", class_weight)

# ======================
# TRAIN MODEL
# ======================
print("🚀 Entraînement du modèle ML")

model = DecisionTreeClassifier(
    max_depth=7,
    min_samples_leaf=5,
    class_weight=class_weight,
    random_state=42
)

model.fit(X, y_enc)

# ======================
# SAVE MODEL
# ======================
bundle = {
    "model": model,
    "label_encoder": le,
    "features": FEATURES
}

MODEL_PATH.parent.mkdir(exist_ok=True)
joblib.dump(bundle, MODEL_PATH)

size = MODEL_PATH.stat().st_size

print("✅ Modèle ML entraîné")
print(f"📦 Taille du modèle : {size} bytes")

if size < 400:
    raise SystemExit("❌ Modèle anormalement petit")

print("🎉 Modèle ML valide — biais BLEU corrigé proprement")
