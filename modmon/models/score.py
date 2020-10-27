"""
Functions to score (calculate metrics for) models in the ModMon database.
"""
import os
import argparse

import pandas as pd
import dateparser

from ..report.report import generate_report
from ..db.schema import Score
from .run import run_model, run_all_models

SCORES_FILE = "scores.csv"
SCORES_COMMAND_ATTR = "score_command"


def add_scores_from_file(
    session, model_version, results_path, dataset_id, run_time, run_id
):
    """Add the values from a model version's metrics file to the database after a new
    run.

    Parameters
    ----------
    session : sqlalchemy.orm.session.Session
        ModMon database session
    model_version : modmon.schema.db.ModelVersion
        Model version object
    results_path : str or Path
       Full path to file containing model metrics (usually called scores.csv)
    dataset_id : int
        ID of the dataset the metrics were calculated for
    run_time : str or datetime.datetime
        Time the model version was run to generate the metrics
    run_id : int
        Run ID to assign to this data

    Raises
    ------
    FileNotFoundError
        If the file model_version.location/scores.csv does not exist
    """

    if not os.path.exists(results_path):
        raise FileNotFoundError(f"{results_path} not found.")

    metrics = pd.read_csv(results_path)

    for _, row in metrics.iterrows():
        metric_name, metric_value = row

        score = Score(
            modelid=model_version.modelid,
            modelversion=model_version.modelversion,
            datasetid=dataset_id,
            isreference=False,
            runtime=run_time,
            runid=run_id,
            metric=metric_name,
            value=metric_value,
        )
        session.add(score)


def score_model(
    model_version,
    start_date=None,
    end_date=None,
    database=None,
    force=False,
    session=None,
    save_to_db=True,
    verbose=True,
    capture_output=False,
    run_dir=None,
):
    """Run a model version's score_command to generate new metrics values with the
    specified dataset inputs.

    Parameters
    ----------
    model_version : modmon.schema.db.ModelVersion
        Model version object
    start_date : str or datetime.datetime , optional
        Dataset start date, by default None
    end_date : str or datetime.datetime , optional
        Dataset end date, by default None
    database : str , optional
        Dataset database name, by default None
    force : bool, optional
        If True regenerate results for a model version even if they already exist in the
        database for the same dataset, by default False
    session : sqlalchemy.orm.session.Session, optional
        ModMon database session or None in which case one will be created, by default
        None
    save_to_db : bool, optional
        If True, save results to the database, by default True
    verbose: bool, optional
        If True print additional progress messages, by default True
    capture_output: bool, optional
        If True capture stdout and stderr of subprocess calls rather than printing to
        console, by default False
    command_attr: str, optional
        Attribute of model_version that contains the model command to run, by default
        'score_command'

    Raises
    ------
    FileNotFoundError
        If the metrics file is not successfully created at
        model_version.location/scores.csv after the model run.
    """
    run_model(
        model_version=model_version,
        command_attr=SCORES_COMMAND_ATTR,
        results_file=SCORES_FILE,
        results_table=Score,
        file_to_db=add_scores_from_file,
        start_date=start_date,
        end_date=end_date,
        database=database,
        force=force,
        session=session,
        save_to_db=save_to_db,
        verbose=verbose,
        capture_output=capture_output,
        run_dir=run_dir,
    )


def score_all_models(
    start_date=None, end_date=None, database=None, force=False, run_inactive=False
):
    """Run all active model versions in the database to generate metrics values for a
    new dataset.

    Parameters
    ----------
    start_date : str or datetime.datetime , optional
        Dataset start date, by default None
    end_date : str or datetime.datetime , optional
        Dataset end date, by default None
    database : str, optional
        Dataset database name, by default None
    force : bool, optional
        If True regenerate results for a model version even if they already exist in the
        database for the same dataset, by default False
    """

    run_all_models(
        command_attr=SCORES_COMMAND_ATTR,
        results_file=SCORES_FILE,
        results_table=Score,
        file_to_db=add_scores_from_file,
        start_date=start_date,
        end_date=end_date,
        database=database,
        force=force,
        run_inactive=run_inactive,
    )


def main():
    """Calculate metrics for all active model versions in the datbase on a new dataset.

    Available from the command-line as modmon_score
    """
    parser = argparse.ArgumentParser(
        description=(
            "Automatically run all active model versions in the monitoring database"
        )
    )
    parser.add_argument("--start_date", help="Start date of dataset")
    parser.add_argument("--end_date", help="End date of dataset")
    parser.add_argument("--database", help="Name of the database to connect to")
    parser.add_argument(
        "--force",
        help="If set, run models even if results already exist in the database",
        action="store_true",
    )
    parser.add_argument(
        "--run_inactive",
        help="If set, also run models marked as inactive",
        action="store_true",
    )

    args = parser.parse_args()
    # TODO currently only deal with dates, not times
    if args.start_date is not None:
        start_date = dateparser.parse(args.start_date).date()
    else:
        start_date = None
    if args.end_date is not None:
        end_date = dateparser.parse(args.end_date).date()
    else:
        end_date = None

    score_all_models(
        start_date,
        end_date,
        args.database,
        force=args.force,
        run_inactive=args.run_inactive,
    )
    generate_report()
