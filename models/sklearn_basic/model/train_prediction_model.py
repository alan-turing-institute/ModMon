from get_data import get_data
import json
import numpy as np
import pandas as pd
import pickle
from sklearn.linear_model import BayesianRidge
import timeit

# Pull the training data into dataframes (imagine this was a database query)
X_train, y_train = get_data()

# Set model parameters
alpha_1=1e-06
alpha_2=1e-06
n_iter=500

# Create and train model and get training time metric
model = BayesianRidge(alpha_1=alpha_1, alpha_2=alpha_2, n_iter=n_iter)
start_model_training = timeit.default_timer()
model.fit(X_train, y_train)
stop_model_training = timeit.default_timer()
training_time = stop_model_training - start_model_training

# Save model to disk
filename = 'model.sav'
pickle.dump(model, open(filename, 'wb'))

# Output metrics as csv
metrics = pd.DataFrame([["training_time", training_time]], columns=["metric", "value"])
metrics.to_csv("data/training_metrics.csv", index=False)
