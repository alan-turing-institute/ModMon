import argparse
import sys

from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError

from schema import Base
from db_connect import DB, PORT, DB_CONNECTION_STRING, ENGINE


def ask_for_confirmation(message):
    answer = input(f"{message} Type 'yes' to continue: ")
    if answer != "yes":
        return False
    else:
        return True


def create_database(db_name=DB, force=False):
    engine = create_engine(f"postgres://localhost:{PORT}/postgres")
    conn = engine.connect()
    conn.execute("commit")
    try:
        conn.execute(f'CREATE DATABASE "{db_name}"')
    except ProgrammingError as e:
        if f'database "{db_name}" already exists' in str(e):
            if force:
                print("Deleting pre-existing database.")
                delete_database(db_name=db_name, force=force)
                print("Creating new database.")
                create_database(db_name=db_name, force=force)
            else:
                print(f'Database "{db_name}" already exists.')
        else:
            raise


def delete_database(db_name=DB, force=False):
    if not force:
        confirmed = ask_for_confirmation(
            "WARNING: This will delete all data currently in the database."
        )
        if not confirmed:
            print("Aborting create.")
            return

    engine = create_engine(f"postgres://localhost:{PORT}/postgres")
    conn = engine.connect()
    conn.execute("commit")
    try:
        conn.execute(f'DROP DATABASE "{db_name}"')
    except ProgrammingError as e:
        if f'database "{db_name}" does not exist' in str(e):
            print(f'There is no database called "{db_name}".')
        else:
            raise


def create_schema(force=False, checkfirst=True):
    if not checkfirst and not force:
        confirmed = ask_for_confirmation(
            "WARNING: This will delete all data currently in the database."
        )
        if not confirmed:
            print("Aborting create.")
            return

    Base.metadata.create_all(ENGINE, checkfirst=checkfirst)


def delete_schema(force=False, checkfirst=True):
    if not force:
        confirmed = ask_for_confirmation(
            "WARNING: This will delete ALL tables and data in the database."
        )
        if not confirmed:
            print("Aborting delete.")
            return

    Base.metadata.drop_all(ENGINE, checkfirst=checkfirst)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create the model monitoring database (ModMon)."
    )
    parser.add_argument(
        "--force",
        help="Delete and recreate the database without asking for confirmation if set",
        action="store_true",
    )
    args = parser.parse_args()

    if not args.force:
        confirmed = ask_for_confirmation(
            "WARNING: This will delete all data in any pre-existing ModMon database."
        )
        if not confirmed:
            print("Aborting create.")
            sys.exit(0)

    create_database(force=True)
    create_schema(force=True, checkfirst=False)
