"""
Check a model contains all the required files and information before submission to the
ModMon database.
"""
import argparse
import os
import json
import subprocess
import re

import colorama
from colorama import Fore
import dateparser
import pandas as pd
from pandas.api.types import is_numeric_dtype

from ..db.connect import get_session, check_connection_ok
from ..db.schema import Team, Model, Modelversion, Researchquestion, Dataset
from ..envs.utils import get_model_env_types
from ..envs.conda import create_conda_env
from ..envs.renv import create_renv_env
from ..models.repro import check_reproduciblity
from ..models.run import build_run_cmd

# reset print colour to default after each use of colorama
colorama.init(autoreset=True)


def print_success(message):
    """Print a success message in green font preceded by a tick mark.

    Parameters
    ----------
    message : str
        Message to print
    """
    print(f"{Fore.GREEN}[✓] {message}")


def print_fail(message):
    """Print a failure message in red font preceded by a cross.

    Parameters
    ----------
    message : str
        Message to print
    """
    print(f"{Fore.RED}[x] {message}")


def print_warn(message):
    """Print a warning message in yellow font preceded by an exclamation mark.

    Parameters
    ----------
    message : str
        Warning message to print
    """
    print(f"{Fore.YELLOW}[!] {message}")


def print_info(message):
    """Print information in white font preceded by an empty [ ] for compatibility with
    print_success, print_error and print_warn.

    Parameters
    ----------
    message : str
        Information to print
    """
    print(f"{Fore.WHITE}[ ] {message}")


def check_metadata_keys(metadata):
    """Check whether metadata contains all the expected keys.

    Parameters
    ----------
    metadata : dict
        Loaded metadata JSON as a dict
    """
    expected_keys = [
        "team",
        "contact",
        "contact_email",
        "research_question",
        "model_name",
        "model_version",
        "db_name",
        "data_window_start",
        "data_window_end",
        "model_train_datetime",
        "model_run_datetime",
        "command",
    ]
    optional_keys = [
        "team_description",
        "model_description",
        "training_data_description",
        "test_data_description",
    ]

    exp_keys_present = [key in metadata.keys() for key in expected_keys]
    opt_keys_present = [key in metadata.keys() for key in optional_keys]
    if all(exp_keys_present) and all(opt_keys_present):
        print_success("Metadata: All keys present")
    else:
        if not all(exp_keys_present):
            missing_keys = [key for key in expected_keys if key not in metadata.keys()]
            print_fail(f"Metadata: Missing required keys - {missing_keys}")
        if not all(opt_keys_present):
            missing_keys = [key for key in optional_keys if key not in metadata.keys()]
            print_warn(f"Metadata: Missing optional keys - {missing_keys}")


def check_metadata_values(metadata):
    """Check whether fields in the metadata have the correct formats.

    Parameters
    ----------
    metadata : dict
        Loaded metadata JSON as a dict
    """
    checked_values = {}

    # email address
    if "contact_email" in metadata.keys():
        checked_values["contact_email"] = (
            True
            if re.fullmatch(
                r"^[^@\s]+@[^@\s]+\.[^@\s]+$", metadata["contact_email"].strip()
            )
            else False
        )

    # datetimes
    datetime_values = [
        "data_window_start",
        "data_window_end",
        "model_train_datetime",
        "model_run_datetime",
    ]
    for key in datetime_values:
        if key in metadata.keys():
            dt = dateparser.parse(metadata[key])
            if dt:
                checked_values[key] = True
            else:
                checked_values[key] = False

    # no specific format but must not be empty
    not_empty_values = [
        "team",
        "contact",
        "research_question",
        "model_name",
        "model_version",
        "db_name",
    ]
    for key in not_empty_values:
        if key in metadata.keys():
            if isinstance(metadata[key], str) and len(metadata[key].strip()) == 0:
                checked_values[key] = False
            else:
                checked_values[key] = True

    # command string - check for placeholders
    if "command" in metadata.keys():
        try:
            build_run_cmd(metadata["command"], "2000-1-1", "2000-1-1", "TEST")
            checked_values["command"] = True
        except ValueError:
            checked_values["command"] = False

    if all(checked_values.values()):
        print_success("Metadata: All keys have valid values")
    else:
        failed_checks = [key for key, check in checked_values.items() if check is False]
        print_fail(f"Metadata: Keys with invalid values - {failed_checks}")


def check_db_for_duplicates(metadata):
    """Check whether the metadata defines entities that are already present in the
    modmon database.

    Parameters
    ----------
    metadata : dict
        Loaded metadata JSON as a dict
    """
    ok, err = check_connection_ok()
    if not ok:
        print_fail(f"Database: Connection failed - {err}")
        return

    session = get_session()
    new_values = []
    dup_values = []

    if "team" in metadata.keys():
        if session.query(Team).filter_by(teamname=metadata["team"]).count() == 0:
            new_values.append("team")
        else:
            dup_values.append("team")

    if "research_question" in metadata.keys():
        if (
            session.query(Researchquestion)
            .filter_by(description=metadata["research_question"])
            .count()
            == 0
        ):
            new_values.append("research_question")
        else:
            dup_values.append("research_question")

    if "db_name" in metadata.keys():
        if (
            session.query(Dataset).filter_by(databasename=metadata["db_name"]).count()
            == 0
        ):
            new_values.append("db_name")
        else:
            dup_values.append("db_name")

    if "model_name" in metadata.keys():
        model = session.query(Model).filter_by(name=metadata["model_name"]).first()
        if not model:
            new_values.append("model_name")
        else:
            dup_values.append("model_name")

            if "model_version" in metadata.keys():
                if (
                    session.query(Modelversion)
                    .filter_by(model=model)
                    .filter_by(modelversion=metadata["model_version"])
                    .count()
                    == 0
                ):
                    new_values.append("model_version")
                    print_success("Database: Unique model name and version combination")
                else:
                    dup_values.append("model_version")
                    print_fail("Database: Model name and version already exist")

    if new_values:
        print_info(f"Database: New entries will be created for {new_values}")
    if dup_values:
        print_warn(f"Database: Entries already exist for {dup_values}")


def check_metrics_file(metrics_path):
    """Check that the metrics file can be loaded and has two columns called "metric" and
    "value".

    Parameters
    ----------
    metrics_path : str
        Path to metrics file
    """
    metrics = pd.read_csv(metrics_path)
    metrics.columns = metrics.columns.str.strip()

    exp_cols = ["metric", "value"]
    if all(metrics.columns == exp_cols):
        print_success("Metrics: Found expected columns")
    else:
        print_fail(
            f"Metrics: Incorrect columns - found {metrics.columns} instead of {exp_cols}"
        )

    print_warn("NOT IMPLEMENTED: Numeric value check")


def check_submission(path, create_envs=False):
    """Run all submission checks on a model directory.

    Parameters
    ----------
    path : str
        Path to model directory
    create_envs : bool, optional
        If True try to create any defined conda or renv environments, by default False
    """
    print_info(f"Checking {path}...")

    # metadata file
    metadata_path = f"{path}/metadata.json"
    if os.path.exists(metadata_path):
        print_success("Metadata: File exists")

        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

            check_metadata_keys(metadata)
            check_metadata_values(metadata)
            check_db_for_duplicates(metadata)

        except json.decoder.JSONDecodeError as e:
            print_fail(f"Metadata: JSON Error - {e}")

    else:
        print_fail("Metadata: File not found")

    metrics_path = f"{path}/metrics.csv"
    if os.path.exists(metrics_path):
        print_success("Metrics: File exists")
        check_metrics_file(metrics_path)
    else:
        print_fail("Metrics: File not found")

    # conda or renv environment
    env_types = get_model_env_types(path)

    if env_types["conda"]:
        print_success("Environment: conda found")

        if create_envs:
            try:
                print_info("Environment: Creating conda env...")
                create_conda_env(
                    "ModMon-TMPCHECK",
                    env_file=f"{path}/environment.yml",
                    capture_output=True,
                    overwrite=True,
                )
                print_success("Environment: conda environment created")
            except subprocess.CalledProcessError as e:
                print_fail(
                    f"Environment: conda creation failed - {e.returncode} {e.stderr}"
                )

    if env_types["renv"]:
        print_success("Environment: renv found")

        if create_envs:
            try:
                print_info("Environment: Creating renv env...")
                create_renv_env(path, capture_output=True)
                print_success("Environment: renv environment created")
            except subprocess.CalledProcessError as e:
                print_fail(
                    f"Environment: renv creation failed - {e.returncode} {e.stderr}"
                )

    if env_types["conda"] and env_types["renv"]:
        print_warn("Environment: Both conda and renv defined")
    elif not (env_types["conda"] or env_types["renv"]):
        print_fail("Environment: No conda or renv environment found")

    print_info(f"Checking metrics.csv reproducibility...")
    check_reproduciblity(path)


def main(): #TODO: add repro check as option
    """Run submission checks for a model.

    Available from the command-line as modmon_model_check.
    """
    parser = argparse.ArgumentParser(
        description="Check whether a directory passes submission checks"
    )
    parser.add_argument("path", help="Directory to check")
    parser.add_argument(
        "--create_envs",
        help="If set, check whether defined conda and renv environments can be created",
        action="store_true",
    )

    args = parser.parse_args()
    check_submission(args.path, create_envs=args.create_envs)
