import argparse
from ..db.connect import get_session
from ..db.schema import Modelversion, Model
import tempfile
import shutil
import subprocess
from ..models.run import run_model
import pandas as pd

# Temporarily get path from args, but then actually just use function within check
# Get start dates and end dates etc from metadata or db
# Load JSON files from catalogue_results dir within temp dir (only should be 2) and compare the metrics csv hashes

def check_reproduciblity(path, model_name):

    session = get_session()

    with tempfile.TemporaryDirectory() as tmpdirname:
        subprocess.run(["git", "init"], check=True, cwd=tmpdirname)

        subprocess.run(["mkdir", tmpdirname + "/data"], check=True)
        subprocess.run(["mkdir", tmpdirname + "/code"], check=True)
        subprocess.run(["mkdir", tmpdirname + "/results"], check=True)
        shutil.copyfile(path + "/metrics.csv", tmpdirname + "/results/metrics.csv")

        subprocess.run(["git", "add", "metrics.csv"], check=True, cwd=tmpdirname + "/results")  # check=True <- creates python exception
        subprocess.run(["git", "commit", "-m", "'add reference result'"], check=True, cwd=tmpdirname)

        subprocess.run(["catalogue", "engage",
                        "--input_data", "data",
                        "--code", "code"
                        ], check=True, cwd=tmpdirname)
        subprocess.run(["catalogue", "disengage",
                        "--input_data", "data",
                        "--code", "code",
                        "--output_data", "results"
                        ], check=True, cwd=tmpdirname)

        # Get active model version for this model
        modelid = session.query(Model).filter_by(name=model_name).first().modelid
        model_version = session.query(Modelversion).filter_by(modelid=modelid).filter_by(active=True).first()

        print(model_version.modelversion, model_version.modelid)

        # run_model(model_version, start_date, end_date, database, force=True, session=session)
