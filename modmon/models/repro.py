import argparse
import json
from os import listdir, mkdir
import shutil
import subprocess
import tempfile

import pandas as pd

from ..db.connect import get_session
from ..db.schema import Modelversion, Model
from .run import run_model


class DummyModelversion:
    """
    Dummy Modelversion class to use to pass a model to run functions without needing a
    database entry.
    """

    modelid = "TMP"
    modelversion = "TMP"

    def __init__(self, location, command):
        """Initialise an instance of DummyModelversion

        Parameters
        ----------
        location : str
            Path to model directory
        command : str
            Command to run model, including <start_date>, <end_date> and <database>
            placeholders.
        """
        self.location = location
        self.command = command


def catalogue_metrics(model_dir, repro_dir):
    """Use the repro-catalogue package to create a directory called catalogue_results
    inside repro_dir containing hashed versions of the data, code and results dirs,
    which in this case are empty except for metrics.csv in results

    Parameters
    ----------
    model_dir : str
        Path to model directory
    repro_dir : str
        Path to directory to store repro-catalogue results
    """
    shutil.copyfile(model_dir + "/metrics.csv", repro_dir + "/results/metrics.csv")

    subprocess.run(
        ["git", "add", "metrics.csv"],
        check=True,
        cwd=repro_dir + "/results",
        capture_output=True,
    )
    try:
        subprocess.run(
            ["git", "commit", "-m", "'add reference result'"],
            check=True,
            cwd=repro_dir,
            capture_output=True,
        )
    except subprocess.CalledProcessError:  # Commit will fail when metrics.csv is added unchanged
        pass

    subprocess.run(
        ["catalogue", "engage", "--input_data", "data", "--code", "code"],
        check=True,
        cwd=repro_dir,
        capture_output=True,
    )
    subprocess.run(
        [
            "catalogue",
            "disengage",
            "--input_data",
            "data",
            "--code",
            "code",
            "--output_data",
            "results",
        ],
        check=True,
        cwd=repro_dir,
        capture_output=True,
    )


def results_match(repro_dir):
    """Check whether the hashes of metrics.csv generated by repro-catalogue match between
    two folders in repro_dir/catalogue_results, which we assume are the reference
    and generated results ordered by date

    Parameters
    ----------
    repro_dir : str
        Path to directory where repro-catalogue results are stored.

    Returns
    -------
    bool
        True if the hashes of the original and generated metrics.csv files match.
    """

    # Get the location of JSON files generated by repro-catalogue
    reference_metrics_file, generated_metrics_file = sorted(
        listdir(repro_dir + "/catalogue_results")
    )

    # Compare the hashes for the metrics csv
    with open(repro_dir + "/catalogue_results/" + reference_metrics_file, "r") as f:
        reference_metrics = json.load(f)
    with open(repro_dir + "/catalogue_results/" + generated_metrics_file, "r") as f:
        generated_metrics = json.load(f)
    if (
        reference_metrics["output_data"]["results"]["results/metrics.csv"]
        == generated_metrics["output_data"]["results"]["results/metrics.csv"]
    ):
        return True
    return False


def reference_result_is_reproducible(path, metadata):
    """Use repro-catalogue to determine whether the model appraisal system generated
    matching metrics for the model to those supplied as reference metrics by the analyst

    Parameters
    ----------
    path : str
        Path to model directory
    metadata : dict
        Contents of metadata JSON file

    Returns
    -------
    bool
        True if the hashes of the original and generated metrics.csv files match.
    """
    session = get_session()

    with tempfile.TemporaryDirectory() as tmpdirname:
        # copy model to temporary directory to avoid overwriting source files
        tmp_model_path = tmpdirname + "/model"
        shutil.copytree(path, tmp_model_path)

        # temporary dir for repro-catalogue results
        tmp_repro_path = tmpdirname + "/repro"
        mkdir(tmp_repro_path)

        subprocess.run(
            ["git", "init"],
            check=True,
            cwd=tmp_repro_path,
            capture_output=True,
        )

        mkdir(tmp_repro_path + "/data")
        mkdir(tmp_repro_path + "/code")
        mkdir(tmp_repro_path + "/results")

        # Use repro-catalogue with reference metrics supplied by analyst
        catalogue_metrics(tmp_model_path, tmp_repro_path)

        # Create a dummy model version to mimic one from the database
        model_version = DummyModelversion(tmp_model_path, metadata["command"])

        # Run the model in reference mode (do not add results to db)
        # This overwrites metrics.csv within the dir supplied to modmon_model_check
        run_model(
            model_version,
            metadata["data_window_start"],
            metadata["data_window_end"],
            metadata["db_name"],
            reference=True,
            session=session,
            verbose=False,
            capture_output=True,
        )

        # Use repro-catalogue with new metrics just generated
        catalogue_metrics(tmp_model_path, tmp_repro_path)

        match_bool = results_match(tmp_repro_path)
    return match_bool
