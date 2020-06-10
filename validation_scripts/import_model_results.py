# Run this script each time an analyst's prediction model is used and generates new results
import argparse
from datetime import datetime
from db_connect import get_connection, get_unique_id
import json
import pandas as pd

# Set up db connection
cnxn = get_connection()
cursor = cnxn.cursor()

########################
### Create variables ###
########################

# TODO: this csv loading is messy, I think we should use a yaml instead (or neatly formatted JSON template)
metadata = pd.read_csv("../models/sklearn_basic/analyst_scripts/metadata.csv") # TODO: sort out file structure so the path isn't hard coded
def get_value(var):
    return list(metadata.loc[metadata['Field'] == var]['Value'])[0]

model = get_value('model_name')
model_version = get_value('model_version')

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

print('Is the model run datafile specified with -r a set of reference results created by the analyst? (y/n)')
response = input()
if response == 'y' or response  == 'Y':
    reference_result = True
    # Get test dataset ID
    cursor.execute("SELECT referenceTestDatasetID FROM modelVersions WHERE modelID=" + str(mid) + " AND modelVersion='" + model_version + "'")
    tstdid = cursor.fetchone()[0]
else:
    reference_result = False
    # New test Dataset:
    tstdid = get_unique_id(cursor, "datasets", "datasetID")
    # Get additional test dataset info
    db_name = prediction_model_metadata["db_name"]
    data_window_start = datetime.fromisoformat(prediction_model_metadata["data_window_start"])
    data_window_end = datetime.fromisoformat(prediction_model_metadata["data_window_end"])
    test_data_description = prediction_model_metadata["test_data_description"]
    cursor.execute('''
    INSERT INTO datasets (datasetID, dataBaseName, dataBaseAccessTime, description, start_date, end_date)
    VALUES
    (?, ?, ?, ?, ?, ?);
    ''', tstdid, db_name, database_access_time, test_data_description, data_window_start, data_window_end)

# Save result
rid = get_unique_id(cursor, "results", "runID")
for metric, value in metrics.items():
    cursor.execute('''
    INSERT INTO results (modelID, modelVersion, testDatasetID, isReferenceResult, runTime, runID, metric, value)
    VALUES
    (?, ?, ?, ?, ?, ?, ?, ?);
    ''', mid, model_version, tstdid, reference_result, database_access_time, rid, metric, value)

cnxn.commit()
cnxn.close()
