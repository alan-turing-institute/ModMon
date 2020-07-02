import os
import warnings

from .renv import create_renv_env
from .conda import get_conda_activate_command, create_conda_env


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
        #  (as well as setting up renv)
        env_cmd = get_conda_activate_command(conda_env)

    if env_types["conda"]:
        env_name = build_env_name(model_version.modelid, model_version.modelversion)
        create_conda_env(env_name, env_file=f"{model_version.location}/environment.yml")
        env_cmd = get_conda_activate_command(env_name)

    return env_cmd
