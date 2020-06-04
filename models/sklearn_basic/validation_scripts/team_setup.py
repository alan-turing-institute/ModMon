# Run this script once, the first time an analyst submits a model
from db_connect import get_connection
import json

cnxn = get_connection()
cursor = cnxn.cursor()

team = 'REG'
contact = 'Ed Chalstrey'
contact_email = 'echalstrey@turing.ac.uk'
team_description = 'A team from The Alan Turing Institute'
research_question = 'Investigate wine quality dataset'
model = 'WineQuality1'
model_description = 'Model to assess wine quality'

# Team:
cursor.execute('''
INSERT INTO teams (teamName, contactName, contactEmail, description)
VALUES
(?, ?, ?, ?);
''', team, contact, contact_email, team_description)

# Research Questions:
cursor.execute('''
INSERT INTO researchQuestions (questionID, description)
VALUES
(1, ?);
''', research_question)

# Metrics:
# Either enter metrics these manually and provide a description or use the
# analyst's output JSONs as here
model_run_metadata = '../analyst_scripts/prediction-model-metadata.json'
with open(model_run_metadata) as json_file:
    prediction_model_metadata = json.load(json_file)
metrics = prediction_model_metadata["metrics"]

model_training_metadata = '../analyst_scripts/prediction-model-training-metadata.json'
with open(model_training_metadata) as json_file:
    prediction_model_training_metadata = json.load(json_file)
training_metrics = prediction_model_training_metadata["metrics"]

# Create a single metrics dictionary
metrics.update(training_metrics)

for metric in metrics:
    cursor.execute('''
    INSERT INTO metrics (metric)
    VALUES
    (?)
    ''', metric)

# Models:
cursor.execute('''
INSERT INTO models (modelID, teamName, questionID, name, description)
VALUES
(1, ?, 1, ?, ?);
''', team, model, model_description)

cnxn.commit()
cnxn.close()
