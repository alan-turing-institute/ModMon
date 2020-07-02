import subprocess
import os
from datetime import datetime
import argparse
import json
import warnings

import pandas as pd
import dateparser
from sqlalchemy import func

from ..db.connect import get_session, get_unique_id
from ..db.schema import Modelversion, Dataset, Result


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


def get_conda_envs():
    output = subprocess.run(["conda", "env", "list"], capture_output=True, check=True)
    lines = output.stdout.decode("utf-8").split("\n")
    envs = [line.split()[0] for line in lines if len(line) > 0]
    envs = [env for env in envs if env != "#"]
    return envs


def conda_env_exists(env_name):
    envs = get_conda_envs()
    return env_name in envs


def create_conda_env(env_name, env_file=None, dependencies=None, overwrite=False):
    if conda_env_exists(env_name):
        if overwrite:
            subprocess.run(
                ["conda", "remove", "-y", "--name", env_name, "--all"], check=True
            )
        else:
            return

    if env_file:
        subprocess.run(
            ["conda", "env", "create", "-n", env_name, "-f", env_file, "--force"],
            check=True,
        )
    elif dependencies:
        subprocess.run(
            [
                "conda",
                "create",
                "-n",
                env_name,
                "-c",
                "conda-forge",
                "-y",
                *dependencies,
            ],
            check=True,
        )
    else:
        raise ValueError("One of env_file and dependencies must be specified.")


def get_conda_activate_command(env_name, conda_path=None):
    if not conda_path:
        conda_path = os.path.dirname(os.environ["CONDA_EXE"])

    # needed for conda activate to work
    source_conda = f"source {conda_path}/../etc/profile.d/conda.sh"
    activate_env = f"conda activate {env_name}"
    command = f"{source_conda} && {activate_env}"

    return command


def remove_conda_env(env_name):
    subprocess.run(["conda", "remove", "--name", env_name, "--all", "-y"], check=True)


def remove_modmon_envs(models=True, r_versions=True):
    envs = get_conda_envs()

    if models:
        [remove_conda_env(env) for env in envs if env.startswith("ModMon-model")]

    if r_versions:
        [remove_conda_env(env) for env in envs if env.startswith("ModMon-R")]


def get_r_version(path):
    with open(f"{path}/renv.lock", "r") as f:
        r_json = json.load(f)

    return r_json["R"]["Version"]


def create_r_conda(r_version, overwrite=False):
    env_name = f"ModMon-R-{r_version}"
    dependencies = [f"r-base={r_version}", "r-renv"]
    create_conda_env(env_name, dependencies=dependencies, overwrite=overwrite)
    return env_name


def create_renv_env(path):
    # Create a conda environment with the version of R specified in the lockfile
    r_version = get_r_version(path)
    conda_name = create_r_conda(r_version)
    conda_cmd = get_conda_activate_command(conda_name)

    renv_cmd = "Rscript -e 'renv::restore()' && Rscript -e 'renv::init()'"
    subprocess.run(f"{conda_cmd} && {renv_cmd}", cwd=path, shell=True, check=True)
    
    return conda_name


def create_env(model_version):
    env_types = get_model_env_types(model_version.location)
    env_cmd = None

    if env_types["renv"] and env_types["conda"]:
        warnings.warn(
            "Both conda and renv environment detected - conda environment will be given priority."
        )

    if env_types["renv"]:
        conda_env = create_renv_env(model_version.location)
        # create_renv_env returns conda environment with appropriate R version
        # (as well as setting up renv)
        env_cmd = get_conda_activate_command(conda_env)

    if env_types["conda"]:
        env_name = build_env_name(model_version.modelid, model_version.modelversion)
        create_conda_env(env_name, env_file=f"{model_version.location}/environment.yml")
        env_cmd = get_conda_activate_command(env_name)

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
            f"{metrics_path} not found. This should be created by running {mv.command}."
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

    # create dataset for this date range and database
    print("Creating dataset entry...")
    dataset_id = create_dataset(session, start_date, end_date, database)

    # run metrics script for all model versions
    for i, mv in enumerate(model_versions):
        print("=" * 30)
        print(
            f"MODEL {i + 1} OUT OF {len(model_versions)}: ID {mv.modelid} VERSION {mv.modelversion}"
        )
        print("=" * 30)

        # Check whether result already exists for this model version and dataset
        if not force and result_exists(
            session, mv.modelid, mv.modelversion, dataset_id
        ):
            print(
                f"DB already contains result for model {mv.modelid}, version {mv.modelversion} on dataset {dataset_id}. Skipping."
            )
            continue

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
        print("RUN_CMD", run_cmd)
        subprocess.run(run_cmd, cwd=mv.location, shell=True, check=True)

        print("Adding results to database...")
        if not os.path.exists(metrics_path):
            raise FileNotFoundError(
                f"{metrics_path} not found. This should be created by running {run_cmd}."
            )

        add_results_from_file(session, mv, dataset_id, run_time)
        session.commit()

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
