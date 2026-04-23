"""
Baseline Logistic Regression model for Irrigation Need prediction.

Responsibilities:
  - Define the feature schema and pipeline
  - Train on demo/data/train.csv
  - Save the fitted pipeline to demo/runs/model.pkl

Run directly to train and persist:
    python3 base_model.py
"""
from __future__ import annotations

import pathlib
import time

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = pathlib.Path(__file__).parent
TRAIN_PATH = BASE_DIR / "data" / "train.csv"
MODEL_PATH = BASE_DIR / "runs/latest" / "model.pkl"

# ---------------------------------------------------------------------------
# Feature schema (from data dictionary)
# ---------------------------------------------------------------------------
TARGET = "Irrigation_Need"
ID_COL = "id"
LABEL_ORDER = ["Low", "Medium", "High"]

NUMERIC_FEATURES = [
    "Soil_pH",
    "Soil_Moisture",
    "Organic_Carbon",
    "Electrical_Conductivity",
    "Temperature_C",
    "Humidity",
    "Rainfall_mm",
    "Sunlight_Hours",
    "Wind_Speed_kmh",
    "Field_Area_hectare",
    "Previous_Irrigation_mm",
]

CATEGORICAL_FEATURES = [
    "Soil_Type",
    "Crop_Type",
    "Crop_Growth_Stage",
    "Season",
    "Irrigation_Type",
    "Water_Source",
    "Mulching_Used",
    "Region",
]

ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


# ---------------------------------------------------------------------------
# Pipeline factory
# ---------------------------------------------------------------------------
def build_pipeline() -> Pipeline:
    """Return an unfitted Logistic Regression pipeline."""
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )
    clf = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",  # handles Low/Medium/High class imbalance
        solver="lbfgs",
        random_state=42,
    )
    return Pipeline(steps=[("preprocessor", preprocessor), ("clf", clf)])


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------
def train(
    train_path: pathlib.Path = TRAIN_PATH,
    model_path: pathlib.Path = MODEL_PATH,
) -> Pipeline:
    """Load training data, fit the pipeline, persist to *model_path*."""
    print(f"Loading training data from {train_path} ...")
    train_df = pd.read_csv(train_path)
    print(f"  Rows: {len(train_df):,}  |  Columns: {train_df.shape[1]}")

    print(f"\nClass distribution:\n{train_df[TARGET].value_counts().sort_index()}\n")

    X = train_df[ALL_FEATURES]
    y = train_df[TARGET]

    pipeline = build_pipeline()
    print("Fitting Logistic Regression ...")
    t0 = time.time()
    pipeline.fit(X, y)
    elapsed = time.time() - t0
    print(f"  Training time: {elapsed:.1f}s")

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    print(f"  Model saved → {model_path}")

    return pipeline


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    train()
