import subprocess
import os
from datetime import datetime
import argparse

import pandas as pd
import dateparser
from sqlalchemy import func

from ..db.connect import get_session
from ..db.utils import get_unique_id
from ..db.schema import Modelversion, Dataset, Result
from ..envs.utils import create_env


def build_run_cmd(raw_cmd, start_date, end_date, database):
    if "<start_date>" not in raw_cmd:
        raise ValueError("Command does not contain <start_date> placeholder")
    if "<end_date>" not in raw_cmd:
        raise ValueError("Command does not contain <end_date> placeholder")
    if "<database>" not in raw_cmd:
        raise ValueError("Command does not contain <database> placeholder")

    return (
        raw_cmd.replace("<start_date>", str(start_date))
        .replace("<end_date>", str(end_date))
        .replace("<database>", database)
    )


def get_model_versions(session):
    return session.query(Modelversion).filter_by(active=True).all()


def get_iso_time():
    return datetime.now().replace(microsecond=0).isoformat()


def create_dataset(session, start_date, end_date, database):
    # check whether matching dataset already exists
    # TODO currently only checks by date, not times
    dataset = (
        session.query(Dataset)
        .filter_by(databasename=database)
        .filter(func.date(Dataset.start_date) == start_date)
        .filter(func.date(Dataset.end_date) == end_date)
        .first()
    )

    # if matching dataset exists return its id
    if dataset:
        return dataset.datasetid

    else:
        # create id for dataset
        dataset_id = get_unique_id(session, Dataset.datasetid)

        # current date and time in iso format
        description = f"Automatically created by ModMon {get_iso_time()}"

        dataset = Dataset(
            datasetid=dataset_id,
            databasename=database,
            description=description,
            start_date=start_date,
            end_date=end_date,
        )
        session.add(dataset)

        return dataset_id


def result_exists(session, model_id, model_version, dataset_id):
    result = (
        session.query(Result)
        .filter_by(modelid=model_id)
        .filter_by(modelversion=model_version)
        .filter_by(testdatasetid=dataset_id)
        .first()
    )

    if result:
        return True
    else:
        return False


def get_metrics_path(model_version):
    return f"{model_version.location}/metrics.csv"


def add_results_from_file(session, model_version, dataset_id, run_time):
    metrics_path = get_metrics_path(model_version)

    if not os.path.exists(metrics_path):
        raise FileNotFoundError(
            f"{metrics_path} not found. This should be created by running {model_version.command}."
        )

    run_id = get_unique_id(session, Result.runid)

    metrics = pd.read_csv(metrics_path)

    for _, row in metrics.iterrows():
        metric_name, metric_value = row

        dataset = Result(
            modelid=model_version.modelid,
            modelversion=model_version.modelversion,
            testdatasetid=dataset_id,
            isreferenceresult=False,
            runtime=run_time,
            runid=run_id,
            metric=metric_name,
            value=metric_value,
        )
        session.add(dataset)


def run_model(model_version, start_date, end_date, database, force=False, session=None):
    if not session:
        session = get_session()
        close_session = True  # if session is created in function, close it in function
    else:
        close_session = False  # if session given, leave it open

    print("Creating dataset...")
    dataset_id = create_dataset(session, start_date, end_date, database)

    # Check whether result already exists for this model version and dataset
    if not force and result_exists(
        session, model_version.modelid, model_version.modelversion, dataset_id
    ):
        print(
            f"DB already contains result for model {model_version.modelid}, version {model_version.modelversion} on dataset {dataset_id}. Skipping."
        )
        return

    print("Creating environment...")
    env_cmd = create_env(
        model_version.location, model_version.modelid, model_version.modelversion
    )

    print("Running metrics script...")
    # delete any pre-existing metrics file
    metrics_path = get_metrics_path(model_version)
    try:
        os.remove(metrics_path)
    except FileNotFoundError:
        pass

    run_cmd = build_run_cmd(model_version.command, start_date, end_date, database)
    if env_cmd is not None:
        run_cmd = f"{env_cmd} && {run_cmd}"

    # run metrics script
    run_time = get_iso_time()
    print("RUN_CMD", run_cmd)
    subprocess.run(run_cmd, cwd=model_version.location, shell=True, check=True)

    print("Adding results to database...")
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(
            f"{metrics_path} not found. This should be created by running {run_cmd}."
        )

    add_results_from_file(session, model_version, dataset_id, run_time)
    session.commit()

    if close_session:
        session.close()


def run_all_models(start_date, end_date, database, force=False):
    # Set up db connection
    print("Connecting to monitoring database...")
    session = get_session()

    # get active model versions from db
    print("Getting active model versions...", end=" ")
    model_versions = get_model_versions(session)
    print(f"found {len(model_versions)} model versions.")

    if len(model_versions) == 0:
        print("No active model versions found. Returning.")
        return

    # run metrics script for all model versions
    for i, mv in enumerate(model_versions):
        print("=" * 30)
        print(
            f"MODEL {i + 1} OUT OF {len(model_versions)}: ID {mv.modelid} VERSION {mv.modelversion}"
        )
        print("=" * 30)

        run_model(mv, start_date, end_date, database, force=force, session=session)

    session.close()


def main():
    parser = argparse.ArgumentParser(
        description="Automatically run all active model versions in the monitoring database"
    )
    parser.add_argument("--start_date", help="Start date of dataset", required=True)
    parser.add_argument("--end_date", help="End date of dataset", required=True)
    parser.add_argument(
        "--database",
        help="Dummy placeholder for database to connect to, not used",
        required=False,
        default="dummydb",
    )
    parser.add_argument(
        "--force",
        help="If set, run models even if results already exist in the database",
        action="store_true",
    )

    args = parser.parse_args()
    # TODO currently only deal with dates, not times
    start_date = dateparser.parse(args.start_date).date()
    end_date = dateparser.parse(args.end_date).date()
    run_all_models(start_date, end_date, args.database, force=args.force)
