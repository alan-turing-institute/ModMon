import argparse
import tempfile
import shutil # copy
import subprocess
# from .run import run_model
import pandas as pd

# Temporarily get path from args, but then sctually just use function within check
# Get start dates and end dates etc from metadat or db
# Load JSON files from catalogue_results dir within temp dir (only should be 2) and compare the metrics csv hashes

parser = argparse.ArgumentParser(
    description="Get model path"
)
parser.add_argument("path", help="Directory to check")

args = parser.parse_args()
path = args.path

with tempfile.TemporaryDirectory() as tmpdirname:
    subprocess.run(["mkdir", tmpdirname + "/data"], check=True)
    subprocess.run(["mkdir", tmpdirname + "/code"], check=True)
    subprocess.run(["mkdir", tmpdirname + "/results"], check=True)
    shutil.copyfile(path + "/metrics.csv", tmpdirname + "/results/metrics.csv")

    # subprocess.run(["git", "add", tmpdirname + "/metrics.csv"], check=True)  # check=True <- creates python exception
    # subprocess.run(["git", "commit", "-m", "'add reference result'"], check=True)
    # subprocess.run(["catalogue engage", "--input_data", "temp_data", "--code", "temp_code"], check=True)
    test = pd.read_csv(tmpdirname +  "/results/metrics.csv")
    print(test)
