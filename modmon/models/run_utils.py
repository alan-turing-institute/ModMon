from datetime import datetime
import os
import subprocess

from sqlalchemy import func

from ..db.schema import ModelVersion, Dataset
from ..db.utils import get_unique_id
from ..envs.utils import create_env


def build_run_cmd(raw_cmd, start_date=None, end_date=None, database=None):
    """Replace placeholder inputs in the model command with given values.

    Parameters
    ----------
    raw_cmd : str
        Raw command, whichs hould contain placeholders <start_date>, <end_date> and
        <database>.
    start_date : str or datetime.datetimie , optional
        Dataset start date to pass to command (metrics script should use this to modify
        database queries to return data restricted to the given date range), by default
        None
    end_date : str or datetime.datetime , optional
        Dataset end date to pass to command (metrics script should use this to modify
        database queries to return data restricted to the given date range), by default
        None
    database : str, optional
        Name of the database to pass to command (metrics script should use this to
        modify the database it connects to), by default None

    Returns
    -------
    str
        Command to run with at least one of the <start_date>, <end_date> and <database>
        placeholders, to be replaced by the input values.

    Raises
    ------
    ValueError
        If raw_cmd does not contain at least one of the <start_date>, <end_date> and
        <database> placeholders.
    """
    placeholders = {
        "<start_date>": start_date,
        "<end_date>": end_date,
        "<database>": database,
    }

    no_placeholders_found = True
    for key, value in placeholders.items():
        if key in raw_cmd and value is None:
            raise ValueError(f"No value given for {key}")
        else:
            no_placeholders_found = False
            raw_cmd = raw_cmd.replace(key, str(value))

    if no_placeholders_found:
        raise ValueError(
            "Command doesn't include any of the possible placeholders: "
            f"{list(placeholders.keys())}"
        )

    return raw_cmd


def get_model_versions(session, get_inactive=False):
    """Get a list of all active model versions from the database.

    Parameters
    ----------
    session : sqlalchemy.orm.session.Session
        ModMon database session
    get_inactive : bool , optional
        If True also return inactive model versions, by default False

    Returns
    -------
    list
        List of ModelVersion objects including all active model versions.
    """
    query = session.query(ModelVersion)
    if not get_inactive:
        query = query.filter_by(active=True)

    return query.all()


def get_iso_time():
    """Get the current time in ISO format

    Returns
    -------
    str
        Current time in ISO format (yyyy-mm-ddThh:mm:ss)
    """
    return datetime.now().replace(microsecond=0).isoformat()


def create_dataset(session, start_date=None, end_date=None, database=None):
    """Create a new Dataset in the database. If a dataset already exists for the
    specified start_date, end_date and database, return the ID of that dataset instead.

    Parameters
    ----------
    session : sqlalchemy.orm.session.Session
        ModMon database session
    start_date : str or datetime.datetime , optional
        Dataset start date, by default None
    end_date : str or datetime.datetime , optional
        Dateaset end date, by default None
    database : str , optional
        Dataset database name, by default None

    Returns
    -------
    int
        ID of the created dataset (or the pre-existing dataset if a dataset matching
        the inputs already exists)

    Raises
    ------
    ValueError
        If none of the start_date, end_date and database are defined
    """
    if start_date is None and end_date is None and database is None:
        raise ValueError(
            "At least one of start_date, end_date and database " "must be defined"
        )

    # query database for a dataset that matches the given inputs
    # TODO currently only checks by date, not times
    query = session.query(Dataset)
    if start_date is not None:
        query = query.filter(func.date(Dataset.start_date) == start_date)
    if end_date is not None:
        query = query.filter(func.date(Dataset.end_date) == end_date)
    if database is not None:
        query = query.filter_by(databasename=database)

    dataset = query.first()

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


def run_model_command(
    model_version,
    command=None,
    command_attr=None,
    start_date=None,
    end_date=None,
    database=None,
    output_file=None,
    verbose=True,
    capture_output=False,
):
    """
    run a command for a model_version in its environment
    """
    if command is None and command_attr is None:
        raise ValueError("Either the 'command' or 'command_attr' argument must be set")
    elif command is not None and command_attr is not None:
        raise ValueError("Only one of 'command' and 'command_attr' must be set")
    elif command_attr is not None:
        command = getattr(model_version, command_attr)

    if verbose:
        print("Creating environment...")
    env_cmd = create_env(
        model_version.location,
        model_version.modelid,
        model_version.modelversion,
        capture_output=capture_output,
    )

    # delete old outputs
    if output_file is not None:
        try:
            os.remove(output_file)
            print(f"Deleted old outputs at {output_file}")
        except FileNotFoundError:
            pass

    run_cmd = build_run_cmd(command, start_date, end_date, database)
    # run command
    if verbose:
        print(f"Running this command:\n{run_cmd}")
    if env_cmd is not None:
        run_cmd = f"{env_cmd} && {run_cmd}"
        if verbose:
            print(f"Running in this environment:\n{env_cmd}")

    if verbose:
        print("--- start subprocess ---")
    subprocess.run(
        run_cmd,
        cwd=model_version.location,
        shell=True,
        check=True,
        capture_output=capture_output,
        executable="/bin/bash",
    )
    if verbose:
        print("--- end subprocess ---")
