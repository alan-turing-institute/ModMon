# Run this script each time an analyst's prediction model is used and generates new results
import argparse
from datetime import datetime
from db_connect import get_connection, get_unique_id
import json
import pandas as pd

# Set up db connection
cnxn = get_connection()
cursor = cnxn.cursor()

#############
### Files ###
#############

parser = argparse.ArgumentParser(
    description="Save model run data to db."
)

parser.add_argument(
    "-m", help="Model data dir"
)

args = parser.parse_args()
if args.m:
    model_path = args.m
else:
    raise RuntimeError("You must supply model data dir with -m")

metadata_script = model_path + "/metadata.csv"
training_metrics_csv =  model_path + "/data/training_metrics.csv"
prediction_metrics_csv =  model_path + "/data/prediction_metrics.csv"

#####################
### Load metadata ###
#####################

metadata = pd.read_csv(metadata_script)
def get_value(var):
    return list(metadata.loc[metadata['Field'] == var]['Value'])[0]

model = get_value('model_name')
model_version = get_value('model_version')

#################
### Load data ###
#################

# Load model train metrics
training_metrics = pd.read_csv(training_metrics_csv)

# Load model run reference metrics
reference_metrics = pd.read_csv(prediction_metrics_csv)

# Create a single metrics dictionary (training and prediction metrics)
metrics = pd.concat([training_metrics, reference_metrics])

#######################
### Save data to db ###
#######################

# Get model ID
cursor.execute("SELECT modelID FROM models WHERE name='" + model + "'")
mid = cursor.fetchone()[0]

print('Is the "model/data/prediction_metrics.csv" a reference result created by the analyst? (y/n)')
response = input()
if response == 'y' or response  == 'Y':
    reference_result = True
    # Get test dataset ID
    cursor.execute("SELECT referenceTestDatasetID FROM modelVersions WHERE modelID=" + str(mid) + " AND modelVersion='" + model_version + "'")
    tstdid = cursor.fetchone()[0]
    model_run_datetime = get_value('model_run_datetime')
else:
    reference_result = False
    # New test Dataset:
    tstdid = get_unique_id(cursor, "datasets", "datasetID")
    # Get additional test dataset info
    db_name = get_value('db_name')
    data_window_start = get_value('data_window_start')
    data_window_end = get_value('data_window_end')
    test_data_description = get_value('test_data_description')
    model_run_datetime = datetime.now().isoformat() # this assumes that the import of model results is done right after the prediction is run
    cursor.execute('''
    INSERT INTO datasets (datasetID, dataBaseName, description, start_date, end_date)
    VALUES
    (?, ?, ?, ?, ?);
    ''', tstdid, db_name, test_data_description, data_window_start, data_window_end)

# Save result
rid = get_unique_id(cursor, "results", "runID")
for index, row in metrics.iterrows():
    metric, value = row
    cursor.execute('''
    INSERT INTO results (modelID, modelVersion, testDatasetID, isReferenceResult, runTime, runID, metric, value)
    VALUES
    (?, ?, ?, ?, ?, ?, ?, ?);
    ''', mid, model_version, tstdid, reference_result, model_run_datetime, rid, metric, value)

cnxn.commit()
cnxn.close()
