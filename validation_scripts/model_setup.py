# Run this script once, the first time an analyst submits a model file (including for a new version of a model)
import argparse
from datetime import datetime
from db_connect import get_connection, get_unique_id
import json
import pandas as pd

# Set up db connection
cnxn = get_connection()
cursor = cnxn.cursor()

#########################
### Extract variables ###
#########################

# TODO: this csv loading is messy, I think we should use a yaml instead (or neatly formatted JSON template)
metadata = pd.read_csv("../models/sklearn_basic/analyst_scripts/metadata.csv") # TODO: sort out file structure so the path isn't hard coded
def get_value(var):
    return list(metadata.loc[metadata['Field'] == var]['Value'])[0]

team = get_value('team')
contact = get_value('contact')
contact_email = get_value('contact_email')
team_description = get_value('team_description')
research_question = get_value('research_question')
model = get_value('model_name')
model_description = get_value('model_description')
model_version = get_value('model_version')

# location = 'models/sklearn_basic/analyst_scripts/finalized_model.sav'
# command = 'python prediction-metrics.py'
active_model_version = True # TODO - set older versions of the same model to False

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

# Load model train metadata and metrics
with open(model_training_metadata) as json_file:
    prediction_model_training_metadata = json.load(json_file)
training_metrics = prediction_model_training_metadata["metrics"]

# Get training dataset info
db_name_training = prediction_model_training_metadata["db_name"]
database_access_time_training = datetime.fromisoformat(prediction_model_training_metadata["database_access_time"])
data_window_start_training = datetime.fromisoformat(prediction_model_training_metadata["data_window_start"])
data_window_end_training = datetime.fromisoformat(prediction_model_training_metadata["data_window_end"])
model_train_datetime = datetime.fromisoformat(prediction_model_training_metadata["model_train_datetime"])
training_data_description = prediction_model_training_metadata["training_data_description"]

# Load model run metadata and metrics
with open(model_run_metadata) as json_file:
    prediction_model_metadata = json.load(json_file)
metrics = prediction_model_metadata["metrics"]

# Get test dataset info
db_name = prediction_model_metadata["db_name"]
database_access_time = datetime.fromisoformat(prediction_model_metadata["database_access_time"])
data_window_start = datetime.fromisoformat(prediction_model_metadata["data_window_start"])
data_window_end = datetime.fromisoformat(prediction_model_metadata["data_window_end"])
test_data_description = prediction_model_metadata["test_data_description"]

# Create a single metrics dictionary (training and prediction metrics)
metrics.update(training_metrics)

#######################
### Save data to db ###
#######################

# Team:
cursor.execute('''
INSERT INTO teams (teamName, contactName, contactEmail, description)
VALUES
(?, ?, ?, ?);
''', team, contact, contact_email, team_description)

# Research Questions:
qid = get_unique_id(cursor, "researchQuestions", "questionID")
cursor.execute('''
INSERT INTO researchQuestions (questionID, description)
VALUES
(?, ?);
''', qid, research_question)

# Metrics:
for metric in metrics:
    cursor.execute('''
    INSERT INTO metrics (metric)
    VALUES
    (?)
    ''', metric)

# Models:
mid = get_unique_id(cursor, "models", "modelID")
cursor.execute('''
INSERT INTO models (modelID, teamName, questionID, name, description)
VALUES
(?, ?, ?, ?, ?);
''', mid, team, qid, model, model_description)

# Training Dataset:
tdid = get_unique_id(cursor, "datasets", "datasetID")
cursor.execute('''
INSERT INTO datasets (datasetID, dataBaseName, dataBaseAccessTime, description, start_date, end_date)
VALUES
(?, ?, ?, ?, ?, ?);
''', tdid, db_name_training, database_access_time_training, training_data_description, data_window_start_training, data_window_end_training)

# Test Dataset:
tstdid = get_unique_id(cursor, "datasets", "datasetID")
cursor.execute('''
INSERT INTO datasets (datasetID, dataBaseName, dataBaseAccessTime, description, start_date, end_date)
VALUES
(?, ?, ?, ?, ?, ?);
''', tstdid, db_name, database_access_time, test_data_description, data_window_start, data_window_end)

# Model Version
cursor.execute('''
INSERT INTO modelVersions (modelID, modelVersion, trainingDatasetID, referenceTestDatasetID, modelTrainTime, active)
VALUES
(?, ?, ?, ?, ?, ?);
''', mid, model_version, tdid, tstdid, model_train_datetime, active_model_version)

cnxn.commit()
cnxn.close()
