import os
import json

import colorama
from colorama import Fore

from ..envs.utils import get_model_env_types


# reset print colour to default after each use of colorama
colorama.init(autoreset=True)


def print_success(message):
    print(f"{Fore.GREEN}[✓] {message}")


def print_fail(message):
    print(f"{Fore.RED}[x] {message}")


def print_info(message):
    print(f"{Fore.YELLOW}[!] {message}")


def check_model(model_path):
    print(f"Checking {model_path}:")

    # metadata file
    metadata_path = f"{model_path}/metadata.json"
    if os.path.exists(metadata_path):
        print_success("Metadata: File exists")

        with open(metadata_path, "r") as f:
            metadata = json.load(f)

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
        
        for key in expected_keys:
            if key in metadata.keys():
                print_success(f"Metadata: '{key}' exists")
            else:
                print_fail(f"Metadata: '{key}' not found") 
        
    else:
        print_fail("Metadata: File not found")

    # conda or renv environment
    env_types = get_model_env_types(model_path)

    if env_types["conda"]:
        print_success("Environment: conda found")
    if env_types["renv"]:
        print_success("Environment: renv found")
    if env_types["conda"] and env_types["renv"]:
        print_info("Environment: Both conda and renv defined")
    if not (env_types["conda"] or env_types["renv"]):
        print_fail("Environment: No conda or renv environment found")


    #  - do things already exist in database?
