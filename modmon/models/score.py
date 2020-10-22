"""
Functions to run models in the ModMon database.
"""
import subprocess
import os
import argparse

import pandas as pd
import dateparser

from ..report.report import generate_report
from ..db.connect import get_session
from ..db.utils import get_unique_id
from ..db.schema import Score
from .run_utils import (
    get_model_versions,
    get_iso_time,
    create_dataset,
    run_model_command,
)


def score_exists(session, model_id, model_version, dataset_id):
    """Check whether the database already contains scores for a model version on a
    given dataset.

    Parameters
    ----------
    session : sqlalchemy.orm.session.Session
        ModMon database session
    model_id : int
        ID of the model to check
    model_version : str
        Version of the model to check
    dataset_id : int
        ID of the dataset to check

    Returns
    -------
    bool
        True if the database contains scores for the specifed model version and
        dataset.
    """
    score = (
        session.query(Score)
        .filter_by(modelid=model_id)
        .filter_by(modelversion=model_version)
        .filter_by(datasetid=dataset_id)
        .first()
    )

    if score:
        return True
    else:
        return False


def get_metrics_path(model_version):
    """Build the path to the expected location of the metrics file.

    Parameters
    ----------
    model_version : modmon.schema.db.ModelVersion
        Model version object


    Returns
    -------
    str
        Expected path to metrics file
    """
    return f"{model_version.location}/scores.csv"


def add_scores_from_file(session, model_version, dataset_id, run_time):
    """Add the values from a model version's metrics file to the database after a new
    run.

    Parameters
    ----------
    session : sqlalchemy.orm.session.Session
        ModMon database session
    model_version : modmon.schema.db.ModelVersion
        Model version object
    dataset_id : int
        ID of the dataset the metrics were calculated for
    run_time : str or datetime.datetime
        Time the model version was run to generate the metrics

    Raises
    ------
    FileNotFoundError
        If the file model_version.location/scores.csv does not exist
    """
    metrics_path = get_metrics_path(model_version)

    if not os.path.exists(metrics_path):
        raise FileNotFoundError(
            f"{metrics_path} not found. "
            f"This should be created by running {model_version.score_command}."
        )

    run_id = get_unique_id(session, Score.runid)

    metrics = pd.read_csv(metrics_path)

    for _, row in metrics.iterrows():
        metric_name, metric_value = row

        dataset = Score(
            modelid=model_version.modelid,
            modelversion=model_version.modelversion,
            datasetid=dataset_id,
            isreference=False,
            runtime=run_time,
            runid=run_id,
            metric=metric_name,
            value=metric_value,
        )
        session.add(dataset)


def run_model_scoring(
    model_version,
    start_date=None,
    end_date=None,
    database=None,
    force=False,
    session=None,
    reference=False,
    verbose=True,
    capture_output=False,
    command_attr="score_command",
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
    reference : bool, optional
        If True, do not add anything to the database, only setup env and run model, by
        default False
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
    if not session:
        session = get_session()
        close_session = True  # if session is created in function, close it in function
    else:
        close_session = False  # if session given, leave it open

    if not reference:
        if verbose:
            print("Creating dataset...")
        dataset_id = create_dataset(session, start_date, end_date, database)

        # Check whether scores already exists for this model version and dataset
        if not force and score_exists(
            session, model_version.modelid, model_version.modelversion, dataset_id
        ):
            if verbose:
                print(
                    f"DB already contains scores for model {model_version.modelid}, "
                    f"version {model_version.modelversion} on dataset {dataset_id}. "
                    "Skipping."
                )
            return

    if verbose:
        print("Running metrics script...")
    # delete any pre-existing metrics file
    metrics_path = get_metrics_path(model_version)
    # run metrics script
    run_time = get_iso_time()

    run_model_command(
        model_version,
        command_attr=command_attr,
        start_date=start_date,
        end_date=end_date,
        database=database,
        output_file=metrics_path,
        verbose=verbose,
        capture_output=capture_output,
    )

    if not reference:
        if verbose:
            print("Adding results to database...")
        if not os.path.exists(metrics_path):
            run_cmd = getattr(model_version, command_attr)
            raise FileNotFoundError(
                f"{metrics_path} not found. "
                f"This should be created by running {run_cmd}."
            )

        add_scores_from_file(session, model_version, dataset_id, run_time)
    session.commit()

    if close_session:
        session.close()


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
    # Set up db connection
    print("Connecting to monitoring database...")
    session = get_session()

    # get active model versions from db
    print("Getting active model versions...", end=" ")
    model_versions = get_model_versions(session, get_inactive=run_inactive)
    print(f"found {len(model_versions)} model versions.")

    if len(model_versions) == 0:
        print("No active model versions found. Returning.")
        return

    # run metrics script for all model versions
    for i, mv in enumerate(model_versions):
        print("=" * 30)
        print(
            f"MODEL {i + 1} OUT OF {len(model_versions)}: "
            f"ID {mv.modelid} VERSION {mv.modelversion}"
        )
        print("=" * 30)

        try:
            run_model_scoring(
                mv, start_date, end_date, database, force=force, session=session
            )
        except subprocess.CalledProcessError as e:
            print(f"FAILED: subprocess error: {e}")
        except FileNotFoundError as e:
            print(f"FAILED: File not found: {e}")
        except ValueError as e:
            print(f"FAILED: ValueError: {e}")

    session.close()


def main():
    """Run all active model versions in the datbase on a new model version.

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
