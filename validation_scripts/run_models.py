import subprocess
import os


def build_env_name(model_id, model_version):
    return f"model-{model_id}-version-{model_version}"


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


def build_run_cmd(raw_cmd, start_date, end_date):
    return (
        raw_cmd.replace("<start_date>", str(start_date))
        .replace("<end_date>", str(end_date))
        .replace("<database>", "TEST")
    )


def main(start_date, end_date):
    # TODO get model versions from db
    model_versions = [
        {
            "model_id": 1,
            "model_version": "1.0.0",
            "location": "/Users/jroberts/GitHub/DECOVID-dataaccess/monitor/models/lightgbm",
            "command": "make clean; make START_DATE=<start_date> END_DATE=<end_date> DATABASE=<database>",
        }
    ]

    for mv in model_versions:
        env_name = build_env_name(mv["model_id"], mv["model_version"])
        create_conda_env(env_name, f"{mv['location']}/environment.yml")
        env_cmd = get_conda_activate_command(env_name)
        run_cmd = build_run_cmd(mv["command"], start_date, end_date)

        # TODO Delete metrics file from previous run

        subprocess.run(
            f"{env_cmd} && {run_cmd}", cwd=mv["location"], shell=True, check=True
        )

        # TODO save results to db


if __name__ == "__main__":
    main(2200, 2500)
