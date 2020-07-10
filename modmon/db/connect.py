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
    try:
        with ENGINE.connect() as _:
            pass
        return (True, None)
    except sqlalchemy.exc.OperationalError as e:
        return (False, e)


def get_session():
    """Get SQLAlchemy session"""
    DBSession = sessionmaker(bind=ENGINE)
    return DBSession()


def main():
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
