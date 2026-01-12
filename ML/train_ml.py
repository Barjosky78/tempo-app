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

print("🤖 Lancement entraînement ML (avec quotas Tempo)")

# ======================
# LOAD DATASET
# ======================
if not DATASET_PATH.exists():
    print("❌ Dataset ML introuvable")
    exit(1)

df = pd.read_json(DATASET_PATH)

print(f"📊 Échantillons disponibles : {len(df)}")
print("🧱 Colonnes dataset :", list(df.columns))

if len(df) < 200:
    print("❌ Dataset insuffisant pour entraîner un modèle fiable")
    exit(1)

# ======================
# FEATURE ENGINEERING
# ======================
print("🛠️ Construction des features ML")

# Date
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

df["weekday"] = df["date"].dt.weekday
df["month"]   = df["date"].dt.month

# Horizon = 0 (historique réel uniquement)
df["horizon"] = 0

# Label
df["label"] = df["color"]

# Harmonisation noms
df["temp"] = df["temperature"]
df["rte"]  = df["rteConsommation"]

# ======================
# FEATURES ML (CLÉS)
# ======================
FEATURES = [
    "temp",
    "coldDays",
    "rte",
    "weekday",
    "month",
    "horizon",

    # 🔥 NOUVELLES FEATURES TEMPO
    "remainingBleu",
    "remainingBlanc",
    "remainingRouge",
    "seasonDayIndex"
]

TARGET = "label"

missing = [c for c in FEATURES + [TARGET] if c not in df.columns]
if missing:
    print("❌ Colonnes manquantes :", missing)
    exit(1)

X = df[FEATURES]
y = df[TARGET]

# ======================
# LABEL ENCODER
# ======================
le = LabelEncoder()
y_enc = le.fit_transform(y)

print("🏷️ Classes apprises :", list(le.classes_))

# ======================
# TRAIN MODEL
# ======================
print("🚀 Entraînement du modèle ML")

model = DecisionTreeClassifier(
    max_depth=7,          # un peu plus profond (logique saisonnière)
    min_samples_leaf=5,   # évite l’overfit
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

size = MODEL_PATH.stat().st_size

print("✅ Modèle ML entraîné")
print(f"📦 Taille du modèle : {size} bytes")

if size < 300:
    print("❌ Modèle anormalement petit")
    exit(1)

print("🎉 Modèle ML valide (Tempo-aware)")
