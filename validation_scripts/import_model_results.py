# Run this script each time an analyst submits a model
import argparse
from datetime import datetime
from db_connect import get_connection
import json

cnxn = get_connection()
cursor = cnxn.cursor()

########################
### File arguments #####
########################

parser = argparse.ArgumentParser(
    description="Save model run data to db."
)

parser.add_argument(
    "-t", help="Model training metadata JSON"
)

parser.add_argument(
    "-r", help="Model run metadata JSON"
)

args = parser.parse_args()
if args.t:
    model_training_metadata = args.t
else:
    raise RuntimeError("You must supply model training data with -t")
if args.r:
    model_run_metadata = args.r
else:
    raise RuntimeError("You must supply model run data with -r")

########################
### Create variables ###
########################

model = "simple sklearn model" # TODO: should these be part of the metadata JSON or decided by the validator?
model_version = "1.0.0"

# Metrics and metadata from model run
# model_run_metadata = '../analyst_scripts/prediction-model-metadata.json'
with open(model_run_metadata) as json_file:
    prediction_model_metadata = json.load(json_file)
metrics = prediction_model_metadata["metrics"]
model_run_datetime = datetime.fromisoformat(prediction_model_metadata["model_run_datetime"])

# Metrics and metadata from model training
# model_training_metadata = '../analyst_scripts/prediction-model-training-metadata.json'
with open(model_training_metadata) as json_file:
    prediction_model_training_metadata = json.load(json_file)
training_metrics = prediction_model_training_metadata["metrics"]

model_train_datetime = datetime.fromisoformat(prediction_model_training_metadata["model_train_datetime"])

# Create a single metrics dictionary
metrics.update(training_metrics)

location = 'models/sklearn_basic/analyst_scripts/finalized_model.sav' # TODO: is it possible to extract this from the argument?
command = 'python prediction-metrics.py'
current_time = datetime.now()
model_is_active = True

#######################
### Save data to db ###
#######################

# Model Version
cursor.execute('''
INSERT INTO modelVersions (modelID, modelVersion, trainingDatasetID, location, command, modelTrainTime, active)
VALUES
(1, ?, 1, ?, ?, ?, ?);
''', model_version, location, command, model_train_datetime, model_is_active)

# Result
for metric, value in metrics.items():
    cursor.execute('''
    INSERT INTO results (modelID, modelVersion, datasetID, runTime, metric, value)
    VALUES
    (1, ?, 1, ?, ?, ?);
    ''', model_version, model_run_datetime, metric, value)

cnxn.commit()
cnxn.close()
