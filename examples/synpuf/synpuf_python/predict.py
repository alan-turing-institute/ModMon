import argparse
import joblib
import pandas as pd

from sklearn.metrics import roc_auc_score

from db import get_data
from preprocess import preprocess

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("--database")
parser.add_argument("--start_date")  # unused
parser.add_argument("--end_date")  # unused
args = parser.parse_args()

# Set up synpuf db connection
df = get_data(args.database)

# predict whether gender is male from condition
y = df["gender"] == "MALE"
X = df["condition"]

# Preprocess condition strings
X = preprocess(X)

# load the classification pipeline
pipe = joblib.load("pipeline.joblib")

# Calculate metrics
acc = pipe.score(X, y)
y_pred = pipe.predict_proba(X)
auc = roc_auc_score(y, y_pred[:, 1])

# Create df of metrics
metrics = pd.DataFrame([["accuracy", acc], ["AUC", auc],], columns=["metric", "value"])
print(metrics)

# Save the metrics to csv:
metrics.to_csv("metrics.csv", index=False, float_format="%.3f")
