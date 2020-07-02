import json
import subprocess

from .conda import create_r_conda, get_conda_activate_command


def get_r_version(path):
    with open(f"{path}/renv.lock", "r") as f:
        r_json = json.load(f)

    return r_json["R"]["Version"]


def create_renv_env(path):
    # Create a conda environment with the version of R specified in the lockfile
    r_version = get_r_version(path)
    conda_name = create_r_conda(r_version)
    conda_cmd = get_conda_activate_command(conda_name)

    renv_cmd = "Rscript -e 'renv::restore()' && Rscript -e 'renv::init()'"
    subprocess.run(f"{conda_cmd} && {renv_cmd}", cwd=path, shell=True, check=True)
    
    return conda_name
