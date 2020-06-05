# Run this script once, the first time an analyst submits a model
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

team = 'REG'
contact = 'Ed Chalstrey'
contact_email = 'echalstrey@turing.ac.uk'
team_description = 'A team from The Alan Turing Institute'
research_question = 'Investigate wine quality dataset'
model = 'WineQuality1'
model_description = 'Model to assess wine quality'

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
cursor.execute("select max(questionID) from researchQuestions")
max_question_id = cursor.fetchone()[0]
if max_question_id: # Generate and ID INT for the question
    qid = max_question_id + 1
else:
    qid = 1

cursor.execute('''
INSERT INTO researchQuestions (questionID, description)
VALUES
(?, ?);
''', qid, research_question)

# Metrics:
# Either enter metrics these manually and provide a description or use the
# analyst's output JSONs as here
# model_run_metadata = '../analyst_scripts/prediction-model-metadata.json'
with open(model_run_metadata) as json_file:
    prediction_model_metadata = json.load(json_file)
metrics = prediction_model_metadata["metrics"]

# model_training_metadata = '../analyst_scripts/prediction-model-training-metadata.json'
with open(model_training_metadata) as json_file:
    prediction_model_training_metadata = json.load(json_file)
training_metrics = prediction_model_training_metadata["metrics"]

db_name = prediction_model_training_metadata["db_name"]
database_version_snapshot_time = datetime.fromisoformat(prediction_model_training_metadata["database_version_snapshot_time"])
data_window_start = datetime.fromisoformat(prediction_model_training_metadata["data_window_start"])
data_window_end = datetime.fromisoformat(prediction_model_training_metadata["data_window_end"])

# Create a single metrics dictionary
metrics.update(training_metrics)

for metric in metrics:
    cursor.execute('''
    INSERT INTO metrics (metric)
    VALUES
    (?)
    ''', metric)

# Models:
cursor.execute("select max(modelID) from models")
max_model_id = cursor.fetchone()[0]
if max_model_id: # Generate and ID INT for the question
    mid = max_model_id + 1
else:
    mid = 1
cursor.execute('''
INSERT INTO models (modelID, teamName, questionID, name, description)
VALUES
(?, ?, 1, ?, ?);
''', mid, team, model, model_description)

# Datasets:
cursor.execute('''
INSERT INTO datasets (datasetID, dataBaseName, dataBaseVersionTime, start_date, end_date)
VALUES
(1, ?, ?, ?, ?);
''', db_name, database_version_snapshot_time, data_window_start, data_window_end)

cnxn.commit()
cnxn.close()
