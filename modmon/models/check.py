import os
import json
import subprocess
import re

import colorama
from colorama import Fore

from ..envs.utils import get_model_env_types
from ..envs.conda import create_conda_env
from ..envs.renv import create_renv_env

# reset print colour to default after each use of colorama
colorama.init(autoreset=True)


def print_success(message):
    print(f"{Fore.GREEN}[✓] {message}")


def print_fail(message):
    print(f"{Fore.RED}[x] {message}")


def print_warn(message):
    print(f"{Fore.YELLOW}[!] {message}")


def print_info(message):
    print(f"[ ] {message}")


def check_metadata_keys(metadata):
    expected_keys = [
        "team",
        "contact",
        "contact_email",
        "team_description",
        "research_question",
        "model_name",
        "model_description",
        "model_version",
        "db_name",
        "data_window_start",
        "data_window_end",
        "model_train_datetime",
        "training_data_description",
        "model_run_datetime",
        "test_data_description",
        "command",
    ]

    keys_present = [key in metadata.keys() for key in expected_keys]
    if all(keys_present):
        print_success("Metadata: All keys present")
    else:
        missing_keys = [key for key in expected_keys if key not in metadata.keys()]
        print_fail(f"Metadata: Missing keys - {missing_keys}")


def check_metadata_values(metadata):
    # valid value and already exists in db or not?
    print_warn("NOT IMPLEMENTED: check_metadata_values")

    checked_values = {}
    checked_values["contact_email"] = re.fullmatch(
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$", metadata["contact_email"]
    )


def check_model(model_path):
    print(f"Checking {model_path}:")

    # metadata file
    metadata_path = f"{model_path}/metadata.json"
    if os.path.exists(metadata_path):
        print_success("Metadata: File exists")

        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

            check_metadata_keys(metadata)
            check_metadata_values(metadata)
        except json.decoder.JSONDecodeError as e:
            print_fail(f"Metadata: JSON Error - {e}")

    else:
        print_fail("Metadata: File not found")

    # conda or renv environment
    env_types = get_model_env_types(model_path)

    if env_types["conda"]:
        print_success("Environment: conda found")

        try:
            print_info("Environment: Creating conda env...")
            create_conda_env(
                "ModMon-TMPCHECK",
                env_file=f"{model_path}/environment.yml",
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

        try:
            print_info("Environment: Creating renv env...")
            create_renv_env(model_path, capture_output=True)
            print_success("Environment: renv environment created")
        except subprocess.CalledProcessError as e:
            print_fail(f"Environment: renv creation failed - {e.returncode} {e.stderr}")

    if env_types["conda"] and env_types["renv"]:
        print_warn("Environment: Both conda and renv defined")
    elif not (env_types["conda"] or env_types["renv"]):
        print_fail("Environment: No conda or renv environment found")

    print_warn("NOT IMPLEMENTED: Run command, check reproducibility")
