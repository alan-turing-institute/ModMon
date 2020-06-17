# Run this script once, the first time an analyst submits a model file (including for a new version of a model)
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
prediction_metrics_csv =  model_path + "/prediction_metrics.csv"

#####################
### Load metadata ###
#####################

with open(metadata_json, 'r') as f:
    metadata = json.load(f)

team = metadata['team']
contact = metadata['contact']
contact_email = metadata['contact_email']
team_description = metadata['team_description']
research_question = metadata['research_question']
model = metadata['model_name']
model_description = metadata['model_description']
model_version = metadata['model_version']

db_name = metadata['db_name']
data_window_start = metadata['data_window_start']
data_window_end = metadata['data_window_end']
model_train_datetime = metadata['model_train_datetime']
training_data_description = metadata['training_data_description']
model_run_datetime = metadata['model_run_datetime']
test_data_description = metadata['test_data_description']

command = metadata['command']

#################
### Load data ###
#################

# Load model run reference metrics
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

def get_list(cursor):
    try:
        fetched = list(cursor.fetchall())
        return [item for sublist in fetched for item in sublist]
    except TypeError:
        return []

# Team:
cursor.execute("SELECT teamName FROM teams")
teams = get_list(cursor)
if team not in teams:
    cursor.execute('''
    INSERT INTO teams (teamName, contactName, contactEmail, description)
    VALUES
    (?, ?, ?, ?);
    ''', team, contact, contact_email, team_description)

# Research Questions:
cursor.execute("SELECT description FROM researchQuestions")
research_questions = get_list(cursor)
if research_question not in research_questions:
    qid = get_unique_id(cursor, "researchQuestions", "questionID")
    cursor.execute('''
    INSERT INTO researchQuestions (questionID, description)
    VALUES
    (?, ?);
    ''', qid, research_question)

# Metrics:
cursor.execute("SELECT metric FROM metrics")
metrics_table = get_list(cursor)
for index, row in metrics.iterrows():
    metric, value = row
    if metric not in metrics_table:
        cursor.execute('''
        INSERT INTO metrics (metric)
        VALUES
        (?)
        ''', metric)

# Models:
cursor.execute("SELECT name FROM models")
models = get_list(cursor)
if model not in models:
    mid = get_unique_id(cursor, "models", "modelID")
    cursor.execute('''
    INSERT INTO models (modelID, teamName, questionID, name, description)
    VALUES
    (?, ?, ?, ?, ?);
    ''', mid, team, qid, model, model_description)

# Model version, training and testing datasets
cursor.execute("SELECT modelID FROM models WHERE name='" + model + "'")
mid = cursor.fetchone()[0]
cursor.execute("SELECT modelVersion FROM modelVersions WHERE modelID=" + str(mid))
model_versions = get_list(cursor)
if model_version not in model_versions:
    # Training Dataset:
    tdid = get_unique_id(cursor, "datasets", "datasetID")
    cursor.execute('''
    INSERT INTO datasets (datasetID, dataBaseName, description, start_date, end_date)
    VALUES
    (?, ?, ?, ?, ?);
    ''', tdid, db_name, training_data_description, data_window_start, data_window_end)

    # Test Dataset:
    tstdid = get_unique_id(cursor, "datasets", "datasetID")
    cursor.execute('''
    INSERT INTO datasets (datasetID, dataBaseName, description, start_date, end_date)
    VALUES
    (?, ?, ?, ?, ?);
    ''', tstdid, db_name, test_data_description, data_window_start, data_window_end)

    # Model Version
    cursor.execute('''
    INSERT INTO modelVersions (modelID, modelVersion, trainingDatasetID, referenceTestDatasetID, location, command, modelTrainTime, active)
    VALUES
    (?, ?, ?, ?, ?, ?, ?, ?);
    ''', mid, model_version, tdid, tstdid, model_path, command, model_train_datetime, True)

    # Set any older versions of the same model as inactive
    cursor.execute("UPDATE modelVersions SET active=FALSE WHERE modelID=" + str(mid) + " AND modelVersion!='" + model_version + "'")

cnxn.commit()
cnxn.close()
