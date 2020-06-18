import subprocess
import os


def get_conda_activate_command(env_name, conda_path=None):
    if not conda_path:
        conda_path = os.path.dirname(os.environ["CONDA_EXE"])

    # needed for conda activate to work
    source_conda = f"source {conda_path}/../etc/profile.d/conda.sh"

    activate_env = f"conda activate {env_name}"

    command = f"{source_conda} && {activate_env}"
    print(command)
    return command


cmd = get_conda_activate_command("wine-lightgbm")

subprocess.run(f"{cmd} && which python", shell=True)
