from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import tempfile

from ..db.connect import get_session
from ..db.schema import ModelVersion
from .run import run_model_command, create_dataset, result_exists, get_iso_time
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


def retrain(model_version, start_date=None, end_date=None, database=None, force=False):
    session = get_session()

    dataset_id = create_dataset(
        session, start_date=start_date, end_date=end_date, database=database
    )

    if (
        result_exists(
            session,
            ModelVersion,
            model_version.model_id,
            model_version.model_version,
            dataset_id,
        )
        and not force
    ):
        print("Model version already trained for this dataset. Skipping.")
        return

    with tempfile.TemporaryDirectory() as tmp_dir:
        # copy model version to a temporary directory
        print("Copying model to temporary directory...")
        shutil.copytree(model_version.location, tmp_dir)

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
        print("Scoring new model...")
        score_model(
            model_version,
            start_date=start_date,
            end_date=end_date,
            database=database,
            force=True,
            session=session,
            save_to_db=False,
        )

        # create new metadata file
        print("Updating metadata...")
        update_metadata(tmp_dir, start_date, end_date, database)

        # add new model version to database (+ set previous inactivce)
        print("Adding new model to database...")
        setup_model(tmp_dir, check_first=False, set_old_inactive=True)

