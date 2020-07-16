"""
Functions for creating and activating renv environments
"""
import json
import subprocess

from .conda import create_r_conda, get_conda_activate_command


def get_r_version(path):
    """Get the version of R specified in the renv.lock file

    Parameters
    ----------
    path : str
        Path to the project directory. The file path/renv.lock must exist.

    Returns
    -------
    str
        R version
    """
    with open(f"{path}/renv.lock", "r") as f:
        r_json = json.load(f)

    return r_json["R"]["Version"]


def create_renv_env(path, capture_output=False):
    """Create a conda environment with the version of R specified in the lockfile, and
    initialise the renv environment, installing all dependencies (within the conda
    environment to ensure the correct version of R is used).

    Parameters
    ----------
    path : str
        Path to project directory containing the renv.lock file
    capture_output : bool, optional
        Passed to subprocess.run, whether to capture stdout and stderr of shell calls,
        by default False

    Returns
    -------
    str
        Name of the created conda environment
    """
    r_version = get_r_version(path)
    conda_name = create_r_conda(r_version)
    conda_cmd = get_conda_activate_command(conda_name)

    renv_cmd = "Rscript -e 'renv::restore()' && Rscript -e 'renv::init()'"
    subprocess.run(
        f"{conda_cmd} && {renv_cmd}",
        cwd=path,
        shell=True,
        check=True,
        capture_output=capture_output,
    )

    return conda_name
