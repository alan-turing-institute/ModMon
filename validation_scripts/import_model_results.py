# Run this script each time an analyst's prediction model is used and generates new results
import argparse
from datetime import datetime
from db_connect import get_connection, get_unique_id
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

model = "WineQuality1" # TODO: should these be part of the metadata JSON or decided by the validator?
model_version = "1.0.0"

# Metrics and metadata from model run
with open(model_run_metadata) as json_file:
    prediction_model_metadata = json.load(json_file)
metrics = prediction_model_metadata["metrics"]
database_access_time = datetime.fromisoformat(prediction_model_metadata["database_access_time"])

# Metrics from model training
with open(model_training_metadata) as json_file:
    prediction_model_training_metadata = json.load(json_file)
training_metrics = prediction_model_training_metadata["metrics"]

# Create a single metrics dictionary
metrics.update(training_metrics)

#######################
### Save data to db ###
#######################

tstdid = 1
mid = 1

# Result
for metric, value in metrics.items():
    cursor.execute('''
    INSERT INTO results (modelID, modelVersion, testDatasetID, runTime, metric, value)
    VALUES
    (?, ?, ?, ?, ?, ?);
    ''', mid, model_version, tstdid, database_access_time, metric, value)

cnxn.commit()
cnxn.close()
