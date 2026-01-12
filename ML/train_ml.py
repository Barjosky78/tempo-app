import json
import pandas as pd
import joblib
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from pathlib import Path

DATASET_PATH = Path("ML/ml_dataset.json")
MODEL_PATH = Path("ML/model.pkl")

print("🤖 Lancement entraînement ML")

# ======================
# LOAD DATASET
# ======================
if not DATASET_PATH.exists():
    print("❌ Dataset ML introuvable")
    exit(1)

df = pd.read_json(DATASET_PATH)
print(f"📊 Échantillons disponibles : {len(df)}")
print("🧱 Colonnes dataset :", list(df.columns))

if len(df) < 50:
    print("❌ Dataset trop petit")
    exit(1)

# ======================
# NORMALISATION COLONNES
# ======================
COLUMN_MAP = {
    "temperature": "temp",
    "rteConsommation": "rte",
    "dayOfWeek": "weekday"
}

for src, dst in COLUMN_MAP.items():
    if src in df.columns and dst not in df.columns:
        df[dst] = df[src]

# ======================
# FEATURES & TARGET
# ======================
FEATURES = ["temp", "rte", "weekday", "month", "horizon"]
TARGET = "label"

missing = [c for c in FEATURES + [TARGET] if c not in df.columns]
if missing:
    print("❌ Colonnes manquantes :", missing)
    exit(1)

X = df[FEATURES]
y = df[TARGET]

# ======================
# ENCODE LABEL
# ======================
le = LabelEncoder()
y_enc = le.fit_transform(y)

# ======================
# TRAIN MODEL
# ======================
model = DecisionTreeClassifier(
    max_depth=6,
    min_samples_leaf=3,
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

joblib.dump(bundle, MODEL_PATH)

print("✅ Modèle ML entraîné")
print("💾 Modèle sauvegardé :", MODEL_PATH)
print("📦 Taille :", MODEL_PATH.stat().st_size, "bytes")
