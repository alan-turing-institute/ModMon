import subprocess
import os


def get_conda_envs():
    output = subprocess.run(["conda", "env", "list"], capture_output=True, check=True)
    lines = output.stdout.decode("utf-8").split("\n")
    envs = [line.split()[0] for line in lines if len(line) > 0]
    envs = [env for env in envs if env != "#"]
    return envs


def conda_env_exists(env_name):
    envs = get_conda_envs()
    return env_name in envs


def create_conda_env(
    env_name, env_file=None, dependencies=None, overwrite=False, capture_output=False
):
    if conda_env_exists(env_name):
        if overwrite:
            subprocess.run(
                ["conda", "remove", "-y", "--name", env_name, "--all"],
                check=True,
                capture_output=capture_output,
            )
        else:
            return

    if env_file:
        subprocess.run(
            ["conda", "env", "create", "-n", env_name, "-f", env_file, "--force"],
            check=True,
            capture_output=capture_output,
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
            capture_output=capture_output,
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


def create_r_conda(r_version, overwrite=False):
    env_name = f"ModMon-R-{r_version}"
    dependencies = [f"r-base={r_version}", "r-renv"]
    create_conda_env(env_name, dependencies=dependencies, overwrite=overwrite)
    return env_name


def remove_conda_env(env_name):
    subprocess.run(["conda", "remove", "--name", env_name, "--all", "-y"], check=True)


def remove_modmon_envs(models=True, r_versions=True):
    envs = get_conda_envs()

    if models:
        [remove_conda_env(env) for env in envs if env.startswith("ModMon-model")]

    if r_versions:
        [remove_conda_env(env) for env in envs if env.startswith("ModMon-R")]
