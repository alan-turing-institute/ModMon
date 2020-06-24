import subprocess
import os
from datetime import datetime
import argparse

import pandas as pd

from db_connect import get_connection, get_unique_id


def get_model_env_types(path):
    if os.path.exists(f"{path}/environment.yml"):
        conda = True
    else:
        conda = False

    if os.path.exists(f"{path}/renv.lock"):
        renv = True
    else:
        renv = False

    return {"conda": conda, "renv": renv}


def build_env_name(model_id, model_version):
    return f"ModMon-model-{model_id}-version-{model_version}"


def conda_env_exists(env_name):
    output = subprocess.run(["conda", "env", "list"], capture_output=True, check=True)
    lines = output.stdout.decode("utf-8").split("\n")
    envs = [line.split()[0] for line in lines if len(line) > 0]
    envs = [env for env in envs if env != "#"]
    return env_name in envs


def create_conda_env(env_name, env_file, overwrite=False):
    if conda_env_exists(env_name):
        if overwrite:
            subprocess.run(
                ["conda", "remove", "-y", "--name", env_name, "--all"], check=True
            )
        else:
            return

    subprocess.run(
        ["conda", "env", "create", "-n", env_name, "-f", env_file, "--force"],
        check=True,
    )


def get_conda_activate_command(env_name, conda_path=None):
    if not conda_path:
        conda_path = os.path.dirname(os.environ["CONDA_EXE"])

    # needed for conda activate to work
    source_conda = f"source {conda_path}/../etc/profile.d/conda.sh"
    activate_env = f"conda activate {env_name}"
    command = f"{source_conda} && {activate_env}"

    return command


def create_renv_env(path):
    # Call out to R with ModMon conda env activated, which has R and renv installed
    modmon_env_cmd = get_conda_activate_command("ModMon")
    renv_cmd = "Rscript -e 'renv::init()'"
    subprocess.run(f"{modmon_env_cmd} && {renv_cmd}", cwd=path, shell=True, check=True)


def create_env(model_version):
    env_types = get_model_env_types(model_version.location)
    env_cmd = None

    if env_types["conda"]:
        env_name = build_env_name(model_version.modelid, model_version.modelversion)
        create_conda_env(env_name, f"{model_version.location}/environment.yml")
        env_cmd = get_conda_activate_command(env_name)

    if env_types["renv"]:
        create_renv_env(model_version.location)

    return env_cmd


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
        .replace("<database>", "TEST")
    )


def get_model_versions(cursor):
    model_versions = cursor.execute(
        "SELECT * FROM modelVersions WHERE active=TRUE"
    ).fetchall()

    return model_versions


def get_iso_time():
    return datetime.now().replace(microsecond=0).isoformat()


def create_dataset(cursor, start_date, end_date, database):
    # create id for dataset
    dataset_id = get_unique_id(cursor, "datasets", "datasetID")

    # current date and time in iso format
    description = f"Automatically created by ModMon {get_iso_time()}"

    cursor.execute(
        """
    INSERT INTO datasets (datasetID, dataBaseName, description, start_date, end_date)
    VALUES (?, ?, ?, ?, ?);
    """,
        dataset_id,
        database,
        description,
        start_date,
        end_date,
    )

    return dataset_id


def get_metrics_path(model_version):
    return f"{model_version.location}/metrics.csv"


def add_results_from_file(cursor, model_version, dataset_id, run_time):
    metrics_path = get_metrics_path(model_version)

    if not os.path.exists(metrics_path):
        raise FileNotFoundError(
            f"{metrics_path} not found. This should be created by running {mv.command}."
        )

    run_id = get_unique_id(cursor, "results", "runID")

    metrics = pd.read_csv(metrics_path)

    for _, row in metrics.iterrows():
        metric_name, metric_value = row
        reference_result = False
        cursor.execute(
            """
        INSERT INTO results (modelID, modelVersion, testDatasetID, isReferenceResult, runTime, runID, metric, value)
        VALUES
        (?, ?, ?, ?, ?, ?, ?, ?);
        """,
            model_version.modelid,
            model_version.modelversion,
            dataset_id,
            reference_result,
            run_time,
            run_id,
            metric_name,
            metric_value,
        )


def main(start_date, end_date, database):
    # Set up db connection
    print("Connecting to monitoring database...")
    cnxn = get_connection()
    cursor = cnxn.cursor()

    # get active model versions from db
    print("Getting active model versions...", end=" ")
    model_versions = get_model_versions(cursor)
    print(f"found {len(model_versions)} model versions.")

    if len(model_versions) == 0:
        print("No active model versions found. Returning.")
        return

    # create dataset for this date range and database
    print("Creating dataset entry...")
    dataset_id = create_dataset(cursor, start_date, end_date, database)

    # run metrics script for all model versions
    for i, mv in enumerate(model_versions):
        print("=" * 30)
        print(
            f"MODEL {i + 1} OUT OF {len(model_versions)}: ID {mv.modelid} VERSION {mv.modelversion}"
        )
        print("=" * 30)

        print("Creating environment...")
        env_cmd = create_env(mv)

        print("Running metrics script...")
        # delete any pre-existing metrics file
        metrics_path = get_metrics_path(mv)
        try:
            os.remove(metrics_path)
        except FileNotFoundError:
            pass

        run_cmd = build_run_cmd(mv.command, start_date, end_date, database)
        if env_cmd is not None:
            run_cmd = f"{env_cmd} && {run_cmd}"

        # run metrics script
        run_time = get_iso_time()
        subprocess.run(run_cmd, cwd=mv.location, shell=True, check=True)

        print("Adding results to database...")
        if not os.path.exists(metrics_path):
            raise FileNotFoundError(
                f"{metrics_path} not found. This should be created by running {run_cmd}."
            )

        add_results_from_file(cursor, mv, dataset_id, run_time)
        cnxn.commit()

    cnxn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Automatically run all active model versions in the monitoring database"
    )
    parser.add_argument("--start_date", help="Start date of dataset", required=True)
    parser.add_argument("--end_date", help="End date of dataset", required=True)
    parser.add_argument(
        "--database",
        help="Dummy placeholder for database to connect to, not used",
        required=False,
        default="TEST",
    )

    args = parser.parse_args()
    main(args.start_date, args.end_date, args.database)
