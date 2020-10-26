from datetime import datetime
import os
import subprocess
from pathlib import Path

from sqlalchemy import func

from ..db.connect import get_session
from ..db.schema import ModelVersion, Dataset
from ..db.utils import get_unique_id
from ..envs.utils import create_env


def result_exists(session, table, model_id, model_version, dataset_id):
    """Check whether the database already contains results in table for the given
    model version and dataset.

    Parameters
    ----------
    session : sqlalchemy.orm.session.Session
        ModMon database session
    table: class
        Table class from modmon.db.schema
    model_id : int
        ID of the model to check
    model_version : str
        Version of the model to check
    dataset_id : int
        ID of the dataset to check

    Returns
    -------
    bool
        True if the database contains results for the specifed model version and
        dataset.
    """
    pred = (
        session.query(table)
        .filter_by(modelid=model_id)
        .filter_by(modelversion=model_version)
        .filter_by(datasetid=dataset_id)
        .first()
    )

    if pred:
        return True
    else:
        return False


def get_model_version_file(model_version, file_path):
    """Build the path to the expected location of a model_version file.

    Parameters
    ----------
    model_version : modmon.schema.db.ModelVersion
        Model version object

    file_path : str
        Path to file (relative to model_version location)

    Returns
    -------
    str
        Expected path to metrics file
    """
    return Path(model_version.location, file_path)


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
    run_dir=None,
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

    if run_dir is None:
        run_dir = model_version.location

    if verbose:
        print("Creating environment...")
    env_cmd = create_env(
        run_dir,
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
        cwd=run_dir,
        shell=True,
        check=True,
        capture_output=capture_output,
        executable="/bin/bash",
    )
    if verbose:
        print("--- end subprocess ---")


def run_model(
    model_version,
    command_attr,
    results_file,
    results_table,
    file_to_db=None,
    start_date=None,
    end_date=None,
    database=None,
    force=False,
    session=None,
    reference=False,
    verbose=True,
    capture_output=False,
):
    """Run a model version's command to generate new results with the specified dataset
    inputs.

    Parameters
    ----------
    model_version : modmon.schema.db.ModelVersion
        Model version object
    command_attr: str
        Attribute of model_version that contains the model command to run
    results_file : str or Path
        Path to file that will be created by running model command
    results_table : class
        Table to save results to from modmon.db.schema
    file_to_db : function , optional
        Function to load results from results_file and add them to the results_table
        table. Must be defined if reference is False. Must take arguments session,
        model_version, results_path, dataset_id, run_time, run_id. By default None.
    start_date : str or datetime.datetime , optional
        Dataset start date, by default None
    end_date : str or datetime.datetime , optional
        Dataset end date, by default None
    database : str , optional
        Dataset database name, by default None
    force : bool, optional
        If True regenerate results for a model version even if they already exist in the
        database for the same dataset, by default False
    session : sqlalchemy.orm.session.Session, optional
        ModMon database session or None in which case one will be created, by default
        None
    reference : bool, optional
        If True, do not add anything to the database, only setup env and run model, by
        default False
    verbose: bool, optional
        If True print additional progress messages, by default True
    capture_output: bool, optional
        If True capture stdout and stderr of subprocess calls rather than printing to
        console, by default False

    Raises
    ------
    FileNotFoundError
        If the metrics file is not successfully created at
        model_version.location/scores.csv after the model run.
    """
    if not session:
        session = get_session()
        close_session = True  # if session is created in function, close it in function
    else:
        close_session = False  # if session given, leave it open

    if not reference:
        if verbose:
            print("Creating dataset...")
        dataset_id = create_dataset(session, start_date, end_date, database)

        # Check whether scores already exists for this model version and dataset
        if not force and result_exists(
            session,
            results_table,
            model_version.modelid,
            model_version.modelversion,
            dataset_id,
        ):
            if verbose:
                print(
                    f"DB already contains results for model {model_version.modelid}, "
                    f"version {model_version.modelversion} on dataset {dataset_id}. "
                    "Skipping."
                )
            return

    if verbose:
        print("Running script...")
    # delete any pre-existing metrics file
    results_path = get_model_version_file(model_version, results_file)
    try:
        os.remove(results_path)
    except FileNotFoundError:
        pass

    # run command
    run_time = get_iso_time()

    run_model_command(
        model_version,
        command_attr=command_attr,
        start_date=start_date,
        end_date=end_date,
        database=database,
        output_file=results_path,
        verbose=verbose,
        capture_output=capture_output,
    )

    if not reference:
        if verbose:
            print("Adding results to database...")
        if not os.path.exists(results_path):
            run_cmd = getattr(model_version, command_attr)
            raise FileNotFoundError(
                f"{results_path} not found. "
                f"This should be created by running {run_cmd}."
            )
        else:
            run_id = get_unique_id(session, results_table.runid)
            file_to_db(
                session, model_version, results_path, dataset_id, run_time, run_id
            )
    session.commit()

    if close_session:
        session.close()


def run_all_models(
    command_attr,
    results_file,
    results_table,
    file_to_db,
    start_date=None,
    end_date=None,
    database=None,
    force=False,
    run_inactive=False,
):
    """Run a command for all models in the database for the specified dataset and save
    them to the database.

    Parameters
    ----------
    command_attr : str
        Attribute of model_version that contains the model command to run
    results_file : str or Path
        Path to file that will be created by running model command
    results_table : class
        Table to save results to from modmon.db.schema
    file_to_db : function
        Function to load results from results_file and add them to the results_table
        table. Must take arguments session, model_version, results_path, dataset_id,
        run_time, run_id. By default None.
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
    model_versions = get_model_versions(session, get_inactive=run_inactive)
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
            run_model(
                model_version=mv,
                command_attr=command_attr,
                results_file=results_file,
                results_table=results_table,
                file_to_db=file_to_db,
                start_date=start_date,
                end_date=end_date,
                database=database,
                force=force,
                session=session,
                reference=False,
                verbose=True,
                capture_output=False,
            )
        except subprocess.CalledProcessError as e:
            print(f"FAILED: subprocess error: {e}")
        except FileNotFoundError as e:
            print(f"FAILED: File not found: {e}")
        except ValueError as e:
            print(f"FAILED: ValueError: {e}")

    session.close()
