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
parser.add_argument('model')
args = parser.parse_args()
model_path = args.model

metadata_json = model_path + "/metadata.json"
training_metrics_csv =  model_path + "/training_metrics.csv"
prediction_metrics_csv =  model_path + "/metrics.csv"

#####################
### Load metadata ###
#####################

with open(metadata_json, 'r') as f:
    metadata = json.load(f)

model = metadata['model_name']
model_version = metadata['model_version']

#################
### Load data ###
#################

# Load model run metrics
metrics = pd.read_csv(prediction_metrics_csv)

# Load model train metrics, if included
try:
    training_metrics = pd.read_csv(training_metrics_csv)
    metrics = pd.concat([training_metrics, metrics]) # Create a single metrics dictionary
except FileNotFoundError:
    pass

#######################
### Save data to db ###
#######################

# Get model ID
cursor.execute("SELECT modelID FROM models WHERE name='" + model + "'")
mid = cursor.fetchone()[0]

print('Is the "metrics.csv" a reference result created by the analyst? (y/n)')
response = input()
if response == 'y' or response  == 'Y':
    reference_result = True
    # Get test dataset ID
    cursor.execute("SELECT referenceTestDatasetID FROM modelVersions WHERE modelID=" + str(mid) + " AND modelVersion='" + model_version + "'")
    tstdid = cursor.fetchone()[0]
    model_run_datetime = metadata['model_run_datetime']
else:
    reference_result = False
    # New test Dataset:
    tstdid = get_unique_id(cursor, "datasets", "datasetID")
    # Get additional test dataset info
    db_name = metadata['db_name']
    data_window_start = metadata['data_window_start']
    data_window_end = metadata['data_window_end']
    test_data_description = metadata['test_data_description']
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
