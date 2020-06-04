# Run this script each time an analyst submits a model
import argparse
from datetime import datetime
from db_connect import get_connection
import json

cnxn = get_connection()
cursor = cnxn.cursor()

########################
### Create variables ###
########################

model = "simple sklearn model" # TODO: should these be part of the metadata JSON or decided by the validator?
model_version = "1.0.0"

# Metrics and metadata from model run
model_run_metadata = '../analyst_scripts/prediction-model-metadata.json'
with open(model_run_metadata) as json_file:
    prediction_model_metadata = json.load(json_file)
metrics = prediction_model_metadata["metrics"]
model_run_datetime = datetime.fromisoformat(prediction_model_metadata["model_run_datetime"])

# Metrics and metadata from model training
model_training_metadata = '../analyst_scripts/prediction-model-training-metadata.json'
with open(model_training_metadata) as json_file:
    prediction_model_training_metadata = json.load(json_file)
training_metrics = prediction_model_training_metadata["metrics"]

model_train_datetime = datetime.fromisoformat(prediction_model_training_metadata["model_train_datetime"])
db_name = prediction_model_training_metadata["db_name"]
database_version_snapshot_time = datetime.fromisoformat(prediction_model_training_metadata["database_version_snapshot_time"])
data_window_start = datetime.fromisoformat(prediction_model_training_metadata["data_window_start"])
data_window_end = datetime.fromisoformat(prediction_model_training_metadata["data_window_end"])

# Create a single metrics dictionary
metrics.update(training_metrics)

location = 'models/sklearn_basic/analyst_scripts/finalized_model.sav' # TODO: is it possible to extract this from the argument?
command = 'python prediction-metrics.py'
current_time = datetime.now()
model_is_active = True

#TODO: split this into a script that runs before and after?

########################
### Arguments idea #####
########################

# parser = argparse.ArgumentParser(
#     description="Save model data to db."
# )
#
# parser.add_argument(
#     "-n", help="Model name"
# )
#
# parser.add_argument(
#     "-v", help="Model version"
# )
#
# args = parser.parse_args()
# if args.n:
#     model = args.n
# if args.v:
#     model_version = args.v


#######################
### Save data to db ###
#######################

# Model Version
cursor.execute('''
INSERT INTO modelVersions (modelID, modelVersion, datasetID, location, command, uploadTime, active)
VALUES
(1, ?, 1, ?, ?, ?, ?);
''', model_version, location, command, current_time, model_is_active)

# Dataset
cursor.execute('''
INSERT INTO datasets (datasetID, dataBaseName, dataBaseVersionTime, start_date, end_date)
VALUES
(1, ?, ?, ?, ?);
''', db_name, database_version_snapshot_time, data_window_start, data_window_end)

# Result
for metric, value in metrics.items():
    cursor.execute('''
    INSERT INTO results (modelID, modelVersion, datasetID, runTime, metric, value)
    VALUES
    (1, ?, 1, ?, ?, ?);
    ''', model_version, model_run_datetime, metric, value)

cnxn.commit()
cnxn.close()
