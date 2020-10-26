import os
from pathlib import Path
import shutil
import tempfile


def retrain(model_version, start_date=None, end_date=None, database=None):

    with tempfile.TemporaryDirectory() as tmp_dir:
        # copy model version to a temporary directory
        shutil.copytree(model_version.location, tmp_dir)

        # delete old outputs
        # TODO old model files
        output_files = ["scores.csv", "predictions.json"]
        for f in output_files:
            f = Path(tmp_dir, f)
            if os.path.exists(f):
                os.remove(f)

        run_model_command(
            model_version,
            command_attr="retrain_command",
            start_date=start_date,
            end_date=end_date,
            database=database,
            output_file=None,
            run_dir=tmp_dir,
        )
