import datetime
from os import devnull
from pathlib import Path
import subprocess

from ..config import config


def generate_report():
    """Generate a html report containing plots found in test_modmon.py"""

    report_dir = config["reports"]["reportdir"]
    print("Generating model appraisal report and saving to", report_dir)
    dev_null = open(devnull, "w")
    date_str = str(datetime.datetime.now())
    subprocess.run(
        ["python", "-m", "unitreport", "--output_file", report_dir + "/model_appraisal_" + date_str + ".html"],
        check=True,
        cwd=Path(Path(__file__).parent),
        stdout=dev_null,
        stderr=dev_null,
    )
