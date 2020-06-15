import argparse
from get_data import get_data
import json
import pickle
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Load the model from disk
model = pickle.load(open("model.sav", 'rb'))

# Pull the test data into dataframes (imagine this was a database query)
X_test, y_test = get_data(test=True)

# Predict with model
predicted_qualities = model.predict(X_test)

# Calculate model prediction metrics
metrics = pd.DataFrame([["r2", r2_score(y_test, predicted_qualities)],
                        ["mse", mean_squared_error(y_test, predicted_qualities)],
                        ["mar", mean_absolute_error(y_test, predicted_qualities)]],
                columns=["metric", "value"])

# Save metrics csv
metrics.to_csv("data/prediction_metrics.csv",  index=False)
