from datetime import datetime
from get_data import get_data
import json
import numpy as np
import pickle
from sklearn.linear_model import BayesianRidge
import timeit

# Pull the training data into dataframes (imagine this was a database query)
X_train, y_train = get_data()

# Imagine these variables were also part of a database query
db_name = 'dummyDB'
database_access_time ='2020-06-03'
data_window_start = '2020-03-03'
data_window_end = '2020-06-03'
training_data_description  = "This is 50% of the wine quality dataset"

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

# Record the time at which the model was trained
model_train_datetime = datetime.now().isoformat()

# Save model to disk
filename = 'finalized_model.sav'
pickle.dump(model, open(filename, 'wb'))

# Output metadata as JSON
metrics = {"training_time": training_time}
output = {"metrics": metrics,
          "model_train_datetime": model_train_datetime,
          "db_name": db_name,
          "database_access_time": database_access_time,
          "data_window_start": data_window_start,
          "data_window_end": data_window_end,
          "training_data_description": training_data_description
          }
with open('prediction-model-training-metadata.json', 'w') as outfile:
    json.dump(output, outfile)
