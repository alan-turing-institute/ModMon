"""
Functions to delete all ModMon artefacts
"""
import argparse

from .utils import ask_for_confirmation
from ..db.create import delete_database
from ..envs.conda import remove_modmon_envs
from ..models.store import delete_all_models_from_storage


def delete_all_artefacts(force=False):
    if not force:
        confirmed = ask_for_confirmation(
            "Deleta all ModMon data (database, models and environments)? "
            "This can't be undone!"
        )
        if not confirmed:
            print("Not confirmed. Aborting.")
            return
        else:
            confirmed = ask_for_confirmation("Are you sure?")
            if not confirmed:
                print("Not confirmed. Aborting.")
                return

    print("Deleting database...")
    delete_database(force=True)
    print("Deleting environments...")
    remove_modmon_envs(models=True, r_versions=True, tmp=True)
    print("Deleting models in storage...")
    delete_all_models_from_storage(force=True)
    print("DONE")


def main():
    parser = argparse.ArgumentParser(
        description="Delete all ModMon artefacts (database, model storage and environments)"
    )
    parser.add_argument(
        "--force",
        help="Delete without asking for confirmation if set",
        action="store_true",
    )
    args = parser.parse_args()

    delete_all_artefacts(force=args.force)
