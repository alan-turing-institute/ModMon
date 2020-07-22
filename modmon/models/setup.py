"""
Functions to add a model version to the ModMon database.

Run this script once, the first time an analyst submits a model file (including for a
new version of a model)
"""
import argparse
import json

import pandas as pd

from ..db.connect import get_session
from ..db.utils import get_unique_id
from ..db.schema import (
    Team,
    Dataset,
    Metric,
    Researchquestion,
    Model,
    Modelversion,
    Result,
)
from .store import copy_model_to_storage


def main():
    """Add a model version to the monitoring database.
    
    Available from the command-line as modmon_model_setup
    """
    # Set up SQLAlchemy session
    session = get_session()

    #############
    # Files ###
    #############

    parser = argparse.ArgumentParser(description="Save model run data to db.")
    parser.add_argument("model")
    args = parser.parse_args()
    model_path = args.model

    metadata_json = model_path + "/metadata.json"
    training_metrics_csv = model_path + "/training_metrics.csv"
    prediction_metrics_csv = model_path + "/metrics.csv"

    #####################
    # Load metadata ###
    #####################

    with open(metadata_json, "r") as f:
        metadata = json.load(f)

    #################
    # Load data ###
    #################

    # Load model run reference metrics
    metrics = pd.read_csv(prediction_metrics_csv)

    # Load model train metrics, if included
    try:
        training_metrics = pd.read_csv(training_metrics_csv)
        metrics = pd.concat(
            [training_metrics, metrics]
        )  # Create a single metrics dictionary
    except FileNotFoundError:
        pass

    #######################
    # Save data to db
    #######################

    # Team:
    teams = [team.teamname for team in session.query(Team).all()]
    if metadata["team"] not in teams:
        newteam = Team(
            teamname=metadata["team"],
            contactname=metadata["contact"],
            contactemail=metadata["contact_email"],
            description=metadata["team_description"],
        )
        session.add(newteam)
        session.commit()

    # Research Questions:
    research_questions = [q.description for q in session.query(Researchquestion).all()]
    if metadata["research_question"] not in research_questions:
        question_id = get_unique_id(session, Researchquestion.questionid)
        newquestion = Researchquestion(
            questionid=question_id, description=metadata["research_question"]
        )
        session.add(newquestion)
        session.commit()
    else:
        question = (
            session.query(Researchquestion)
            .filter_by(description=metadata["research_question"])
            .first()
        )
        question_id = question.questionid

    # Metrics:
    metrics_in_db = [metric.metric for metric in session.query(Metric).all()]
    for index, row in metrics.iterrows():
        metric, value = row
        if metric not in metrics_in_db:
            newmetric = Metric(metric=metric)
            session.add(newmetric)
            session.commit()

    # Models:
    models = [model.name for model in session.query(Model).all()]
    if metadata["model_name"] not in models:
        model_id = get_unique_id(session, Model.modelid)
        newmodel = Model(
            modelid=model_id,
            teamname=metadata["team"],
            questionid=question_id,
            name=metadata["model_name"],
            description=metadata["model_description"],
        )
        session.add(newmodel)
        session.commit()
    else:
        model = session.query(Model).filter_by(name=metadata["model_name"]).first()
        model_id = model.modelid

    # Model version, training and testing datasets
    model_versions = [
        model.modelversion
        for model in session.query(Modelversion).filter_by(modelid=model_id).all()
    ]
    if metadata["model_version"] not in model_versions:
        # Training Dataset:
        training_dataset_id = get_unique_id(session, Dataset.datasetid)
        training_dataset = Dataset(
            datasetid=training_dataset_id,
            databasename=metadata["db_name"],
            description=metadata["training_data_description"],
            start_date=metadata["data_window_start"],
            end_date=metadata["data_window_end"],
        )
        session.add(training_dataset)
        session.commit()

        # Test Dataset:
        test_dataset_id = get_unique_id(session, Dataset.datasetid)
        test_dataset = Dataset(
            datasetid=test_dataset_id,
            databasename=metadata["db_name"],
            description=metadata["test_data_description"],
            start_date=metadata["data_window_start"],
            end_date=metadata["data_window_end"],
        )
        session.add(test_dataset)
        session.commit()

        # Copy model files to storage
        modmon_model_path = copy_model_to_storage(
            model_path, model_id, metadata["model_version"]
        )

        # Model Version
        model_version = Modelversion(
            modelid=model_id,
            modelversion=metadata["model_version"],
            trainingdatasetid=training_dataset_id,
            referencetestdatasetid=test_dataset_id,
            location=str(modmon_model_path),
            command=metadata["command"],
            modeltraintime=metadata["model_train_datetime"],
            active=True,
        )
        session.add(model_version)
        session.commit()

        # Set any older versions of the same model as inactive
        old_versions_this_model = (
            session.query(Modelversion)
            .filter_by(modelid=model_id)
            .filter(Modelversion.modelversion != metadata["model_version"])
            .all()
        )
        for old_model_version in old_versions_this_model:
            old_model_version.active = False
            session.commit()

        # Save analyst reference result for this model version
        run_id = get_unique_id(session, Result.runid)
        for index, row in metrics.iterrows():
            metric, value = row
            reference_result = Result(
                modelid=model_id,
                modelversion=metadata["model_version"],
                testdatasetid=test_dataset_id,
                isreferenceresult=True,
                runtime=metadata["model_run_datetime"],
                runid=run_id,
                metric=metric,
                value=value,
            )
            session.add(reference_result)
            session.commit()
