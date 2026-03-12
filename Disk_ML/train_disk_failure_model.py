import polars as pl
import pandas as pd
import xgboost as xgb
import joblib
import glob
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score


# ==============================
# CONFIG
# ==============================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, "backblaze", "*.csv")
MODEL_OUTPUT = os.path.join(SCRIPT_DIR, "disk_failure_model_gpu.pkl")

# Most predictive SMART attributes
SMART_FEATURES = [
    "smart_1_raw",
    "smart_5_raw",
    "smart_7_raw",
    "smart_9_raw",
    "smart_187_raw",
    "smart_188_raw",
    "smart_193_raw",
    "smart_194_raw",
    "smart_197_raw",
    "smart_198_raw"
]

BASE_COLUMNS = ["date", "model", "failure"]

COLUMNS = BASE_COLUMNS + SMART_FEATURES


# ==============================
# LOAD DATA WITH POLARS LAZY
# ==============================

print("Scanning CSV files with Polars lazy mode...")

df = pl.scan_csv(DATA_PATH)

# select only useful columns
df = df.select(COLUMNS)

# fill missing values
df = df.fill_null(0)

print("Collecting dataset into memory...")

df = df.collect()

print("Dataset shape:", df.shape)


# ==============================
# CONVERT TO PANDAS
# ==============================

print("Converting to pandas...")

data = df.to_pandas()


# ==============================
# OPTIONAL: DOWNSAMPLE HEALTHY DRIVES
# ==============================

print("Balancing dataset...")

failures = data[data["failure"] == 1]
healthy = data[data["failure"] == 0]

# keep all failures but only 10% healthy
healthy_sample = healthy.sample(frac=0.1, random_state=42)

data = pd.concat([failures, healthy_sample])

print("Balanced dataset size:", data.shape)


# ==============================
# ENCODE MODEL TYPE
# ==============================

print("Encoding drive models...")

data = pd.get_dummies(data, columns=["model"])


# ==============================
# FEATURES / LABEL
# ==============================

target = "failure"

X = data.drop(columns=[target, "date"])
y = data[target]

print("Feature matrix shape:", X.shape)


# ==============================
# TRAIN TEST SPLIT
# ==============================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    stratify=y,
    random_state=42
)


# ==============================
# TRAIN CUDA MODEL
# ==============================

print("Training GPU XGBoost model...")

model = xgb.XGBClassifier(
    n_estimators=400,
    max_depth=8,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    tree_method="gpu_hist",
    predictor="gpu_predictor",
    eval_metric="logloss",
    random_state=42
)

model.fit(X_train, y_train)


# ==============================
# EVALUATE MODEL
# ==============================

print("\nEvaluating model...")

pred = model.predict(X_test)
prob = model.predict_proba(X_test)[:,1]

print(classification_report(y_test, pred))

auc = roc_auc_score(y_test, prob)
print("ROC AUC:", auc)


# ==============================
# FEATURE IMPORTANCE
# ==============================

print("\nTop predictive features:")

importance = pd.Series(
    model.feature_importances_,
    index=X.columns
).sort_values(ascending=False)

print(importance.head(20))


# ==============================
# SAVE MODEL
# ==============================

joblib.dump(model, MODEL_OUTPUT)

print("\nModel saved:", MODEL_OUTPUT)


# ==============================
# SAMPLE PREDICTION
# ==============================

sample = X_test.iloc[0:1]

prob = model.predict_proba(sample)[0][1]

print("\nExample predicted failure probability:", prob)

print("\nTraining complete.")