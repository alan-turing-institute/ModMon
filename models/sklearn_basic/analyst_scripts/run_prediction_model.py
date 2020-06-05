from datetime import datetime
from get_data import get_data
import json
import pickle
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Load the model from disk
filename = "finalized_model.sav" # TODO: make this an arg for this script
model = pickle.load(open(filename, 'rb'))

# Pull the test data into dataframes (imagine this was a database query)
X_test, y_test = get_data(test=True)

# Imagine these variables were also part of a database query
db_name = 'dummyDB'
data_window_start = '2020-03-03'
data_window_end = '2020-06-03'

# Predict with model
predicted_qualities = model.predict(X_test)

# Calculate model prediction metrics
metrics = {"r2": r2_score(y_test, predicted_qualities),
           "mse": mean_squared_error(y_test, predicted_qualities),
           "mar": mean_absolute_error(y_test, predicted_qualities)
           }

# Record the time at which the model was run
model_run_datetime = datetime.now().isoformat() # this can also be considered the database_version_snapshot_time

# Output as JSON
output = {"metrics": metrics,
          "model_run_datetime": model_run_datetime,
          "db_name": db_name,
          "data_window_start": data_window_start,
          "data_window_end": data_window_end
          }
with open('prediction-model-metadata.json', 'w') as outfile:
    json.dump(output, outfile)
