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
    shutil.copyfile(path + "/metrics.csv", tmpdirname + "/metrics.csv")
    test = pd.read_csv(tmpdirname +  "/metrics.csv")
    print(test)
