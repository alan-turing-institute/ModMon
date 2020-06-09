# Run this script each time an analyst's prediction model is used and generates new results
import argparse
from datetime import datetime
from db_connect import get_connection, get_unique_id
import json

# Set up db connection
cnxn = get_connection()
cursor = cnxn.cursor()

########################
### Create variables ###
########################

model = "WineQuality1" # TODO: should these be part of the metadata JSON or decided by the validator?
model_version = "1.0.0"
tstdid = 1 # TODO: the test data dataset ID will need to be selected as a row already in the datasets table OR a new  row needs to be added

print('Is the model run datafile specified with -r a set of reference results created by the analyst? (y/n)')
response = input()
if response == 'y' or response  == 'Y':
    reference_result = True
else:
    reference_result = False

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

####################################
### Load data from analyst files ###
####################################

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

# Get model ID
cursor.execute("SELECT modelID FROM models WHERE name='" + model + "'")
mid = cursor.fetchone()[0]

# Save result
for metric, value in metrics.items():
    cursor.execute('''
    INSERT INTO results (modelID, modelVersion, testDatasetID, isReferenceResult, runTime, metric, value)
    VALUES
    (?, ?, ?, ?, ?, ?, ?);
    ''', mid, model_version, tstdid, reference_result, database_access_time, metric, value)

cnxn.commit()
cnxn.close()
