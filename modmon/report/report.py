import datetime
from pathlib import Path
import subprocess
import shutil

from ..config import config
from ..utils.utils import ask_for_confirmation


def generate_report():
    """Generate a html report containing plots found in test_modmon.py"""
    report_dir = config["reports"]["reportdir"]
    print("Generating model appraisal report and saving to", report_dir)
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    subprocess.run(
        [
            "python",
            "-m",
            "unitreport",
            "--output_file",
            report_dir + "/model_appraisal_" + date_str + ".html",
            "--templates_dir",
            "templates",
        ],
        check=True,
        cwd=Path(__file__).parent,
        capture_output=True,
    )


def delete_all_reports_from_storage(
    report_dir=config["reports"]["reportdir"],
    force=False,
):
    """Delete all reports in storage.

    Parameters
    ----------
    report_dir : str, optional
        Path to the report storage directory, by default config["reports"]["reportdir"]
    force : bool, optional
        If True delete without asking for confirmation, by default False
    """
    if not force:
        confirmed = ask_for_confirmation(
            "Delete all models in storage? This can't be undone!"
        )
        if not confirmed:
            print("Not confirmed. Aborting.")
            return

    shutil.rmtree(report_dir)


def main():
    """Generate the html report for existing data in the ModMon DB.

    Available from the command-line as modmon_report
    """
    generate_report()
