import json
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

print("🤖 Lancement entraînement ML")

# ======================
# LOAD DATASET
# ======================
DATASET_PATH = "ML/ml_dataset.json"
MODEL_PATH = "ML/model.pkl"

with open(DATASET_PATH, "r") as f:
    data = json.load(f)

print(f"📊 Échantillons disponibles : {len(data)}")

if len(data) < 50:
    raise Exception("❌ Pas assez de données pour entraîner le modèle")

# ======================
# PREPARE DATA
# ======================
df = pd.DataFrame(data)

FEATURES = [
    "temp",
    "coldDays",
    "rte",
    "weekday",
    "month",
    "horizon"
]

TARGET = "color"

X = df[FEATURES]
y = df[TARGET]

# ======================
# ENCODE LABELS
# ======================
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# ======================
# SPLIT
# ======================
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42
)

# ======================
# TRAIN MODEL
# ======================
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    random_state=42
)

model.fit(X_train, y_train)

score = model.score(X_test, y_test)
print(f"✅ Précision ML : {round(score*100,2)} %")

# ======================
# SAVE MODEL
# ======================
bundle = {
    "model": model,
    "label_encoder": le,
    "features": FEATURES,
    "accuracy": score
}

joblib.dump(bundle, MODEL_PATH)

print(f"💾 Modèle ML sauvegardé : {MODEL_PATH}")
