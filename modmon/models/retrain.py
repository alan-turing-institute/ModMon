import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import dateparser

from ..db.connect import get_session
from ..db.schema import ModelVersion
from .run import run_model_command, create_dataset, result_exists, get_iso_time, get_model_versions
from .score import score_model
from .setup import setup_model


def increment_version_str(version_str):
    sub_versions = version_str.split(".")
    sub_versions[-1] = str(int(sub_versions[-1]) + 1)
    return ".".join(sub_versions)


def update_metadata(metadata_dir, start_date, end_date, database):
    metadata_path = Path(metadata_dir, "metadata.json")
    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    metadata["model_version"] = increment_version_str(metadata["model_version"])
    retrain_datetime = get_iso_time()
    metadata["model_train_datetime"] = retrain_datetime
    metadata["model_run_datetime"] = retrain_datetime
    metadata["data_window_start"] = str(start_date)
    metadata["data_window_end"] = str(end_date)
    metadata["db_name"] = database
    metadata["training_data_description"] = "Automatically created by ModMon"
    metadata["test_data_description"] = ""

    with open(metadata_path, "w") as f:
        json.dump(metadata, f)


def retrain_model(
    model_version, start_date=None, end_date=None, database=None, force=False
):
    session = get_session()

    dataset_id = create_dataset(
        session, start_date=start_date, end_date=end_date, database=database
    )

    if (
        result_exists(
            session,
            ModelVersion,
            model_version.modelid,
            model_version.modelversion,
            dataset_id,
        )
        and not force
    ):
        print("Model version already trained for this dataset. Skipping.")
        return

    with tempfile.TemporaryDirectory() as tmp_dir:
        # copy model version to a temporary directory
        print("Copying model to temporary directory...")
        shutil.copytree(model_version.location, tmp_dir, dirs_exist_ok=True)

        # delete old outputs
        # TODO delete old model files
        print("Deleting old output files...")
        output_files = ["scores.csv", "predictions.json"]
        for f in output_files:
            f = Path(tmp_dir, f)
            if os.path.exists(f):
                os.remove(f)

        # retrain model
        print("Retraining model...")
        run_model_command(
            model_version,
            command_attr="retrain_command",
            start_date=start_date,
            end_date=end_date,
            database=database,
            output_file=None,
            run_dir=tmp_dir,
        )

        # score new model (without adding result to database at this stage
        # NOTE: Removed - expect retrain command to save training scores
        # print("Scoring new model...")
        # score_model(
        #    model_version,
        #    start_date=start_date,
        #    end_date=end_date,
        #    database=database,
        #    force=True,
        #    session=session,
        #    save_to_db=False,
        #    run_dir=tmp_dir,
        # )

        # create new metadata file
        print("Updating metadata...")
        update_metadata(tmp_dir, start_date, end_date, database)

        # add new model version to database (+ set previous inactivce)
        print("Adding new model to database...")
        setup_model(tmp_dir, check_first=False, set_old_inactive=True, session=session)


def retrain_all_models(
    start_date=None,
    end_date=None,
    database=None,
    force=False,
    retrain_inactive=False,
):
    """Retrain all models in the database for the specified dataset and save
    the new models to the database.

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
    print("Getting model versions...", end=" ")
    model_versions = get_model_versions(session, get_inactive=retrain_inactive)
    print(f"found {len(model_versions)} model versions.")

    if len(model_versions) == 0:
        print("No model versions found. Returning.")
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
            retrain_model(
                mv,
                start_date=start_date,
                end_date=end_date,
                database=database,
                force=force,
            )
        except subprocess.CalledProcessError as e:
            print(f"FAILED: subprocess error: {e}")
        except FileNotFoundError as e:
            print(f"FAILED: File not found: {e}")
        except ValueError as e:
            print(f"FAILED: ValueError: {e}")

    session.close()


def main():
    """Run predictions for all active model versions in the datbase on a new dataset.

    Available from the command-line as modmon_prediction
    """
    parser = argparse.ArgumentParser(
        description=(
            "Automatically retrain all active model versions in the monitoring database"
        )
    )
    parser.add_argument("--start_date", help="Start date of dataset")
    parser.add_argument("--end_date", help="End date of dataset")
    parser.add_argument("--database", help="Name of the database to connect to")
    parser.add_argument(
        "--force",
        help=(
            "If set, retrain models even if they were trained on the " 
            "same dataset previously"
        ),
        action="store_true",
    )
    parser.add_argument(
        "--run_inactive",
        help="If set, also retrain models marked as inactive",
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

    retrain_all_models(
        start_date=start_date,
        end_date=end_date,
        database=args.database,
        force=args.force,
        retrain_inactive=args.run_inactive,
    )
