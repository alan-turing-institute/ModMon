# Run this script once, the first time an analyst submits a model file (including for a new version of a model)
import argparse
from datetime import datetime
from db_connect import get_connection, get_unique_id
import json
import pandas as pd
from schema import (Base,
                    Team,
                    Dataset,
                    Metric,
                    Researchquestion,
                    Model,
                    Modelversion)
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Set up db connection
cnxn = get_connection()
cursor = cnxn.cursor()

# TODO: edit this so not specific username
Base.metadata.bind = create_engine('postgresql://echalstrey@localhost:5432/ModMon')
DBSession = sessionmaker()
session = DBSession()

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
teams = [team.teamname for team in session.query(Team).all()]
if metadata['team'] not in teams:
    newteam = Team(teamname = metadata['team'],
                   contactname = metadata['contact'],
                   contactemail = metadata['contact_email'],
                   description = metadata['team_description'])
    session.add(newteam)
    session.commit()

# Research Questions:
research_questions = [q.description for q in session.query(Researchquestion).all()]
if metadata['research_question'] not in research_questions:
    #TODO: use sqlalchemy for this function:
    qid = get_unique_id(cursor, "researchQuestions", "questionID")
    newquestion = Researchquestion(questionid = qid,
                                   description = metadata['research_question'])
    session.add(newquestion)
    session.commit()
else:
    question = session.query(Researchquestion).filter_by(description=metadata['research_question']).first()
    qid = question.questionid

# Metrics:
metrics_in_db = [metric.metric for metric in session.query(Metric).all()]
for index, row in metrics.iterrows():
    metric, value = row
    if metric not in metrics_in_db:
        newmetric = Metric(metric = metric)
        session.add(newmetric)
        session.commit()

# Models:
models = [model.name for model in session.query(Model).all()]
if metadata['model_name'] not in models:
    mid = get_unique_id(cursor, "models", "modelID")
    newmodel = Model(modelid = mid,
                     teamname = metadata['team'],
                     questionid = qid,
                     name = metadata['model_name'],
                     description = metadata['model_description'])
    session.add(newmodel)
    session.commit()


# Model version, training and testing datasets
cursor.execute("SELECT modelID FROM models WHERE name='" +  metadata['model_name'] + "'")
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
