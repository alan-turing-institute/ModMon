"""
Functions for connecting to the ModMon database.
"""
# import pyodbc
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, inspect

from .schema import Base


# TODO Deal with DB config correctly, including username ans passwords if needed
# and including details for postgres user on postgres database (for db creation).
#  Should be defined in a config file.
PORT = "5432"
DB = "ModMon"

DB_CONNECTION_STRING = f"postgresql://localhost:{PORT}/{DB}"

ENGINE = create_engine(DB_CONNECTION_STRING)
Base.metadata.bind = ENGINE


def check_connection_ok():
    """Test that connecting to the ModMon database is successful.

    Returns
    -------
    tuple
        Length 2 tuple, where first element is a bool (True is connection successful),
        and second element is a sqlalchemy.exc.OperationalError containing details of
        any exception.
    """
    try:
        with ENGINE.connect() as _:
            pass
        return (True, None)
    except sqlalchemy.exc.OperationalError as e:
        return (False, e)


def get_session():
    """Get a SQLAlchemy session bound to the ModMon database.

    Returns
    -------
    sqlalchemy.orm.session.Session
        ModMon database session.
    """
    DBSession = sessionmaker(bind=ENGINE)
    return DBSession()


def main():
    """Check connection to the ModMon database and, if successful, print the tables and
    columns it contains.
    
    To be used from command line as modmon_db_check
    """
    ok, error = check_connection_ok()
    if not ok:
        print(f"Connecting to the database failed with exception {error}")

    inspector = inspect(ENGINE)
    for table_name in inspector.get_table_names():
        print("=" * 30)
        print("TABLE:   ", table_name)
        print("COLUMNS: ", end=" ")
        columns = inspector.get_columns(table_name)
        for i, column in enumerate(columns):
            if i == len(columns) - 1:
                end = "\n"
            else:
                end = ", "
            print(column["name"], end=end)
