# import pyodbc
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy.exc import ProgrammingError

from schema import Base


# TODO Deal with DB config correctly, including username ans passwords if needed
# and including details for postgres user on postgres database (for db creation).
#  Should be defined in a config file.
PORT = "5432"
DB = "ModMon"

DB_CONNECTION_STRING = f"postgresql://localhost:{PORT}/{DB}"

ENGINE = create_engine(DB_CONNECTION_STRING)
Base.metadata.bind = ENGINE


def get_unique_id(session, column):
    """Get value one higher than the highest value in a SQL table column,
    where the column should be the SQL alchemy table column, e.g. Dataset.datasetid"""
    max_id = session.query(func.max(column)).scalar()
    if max_id:
        return max_id + 1
    return 1


def get_session():
    """Get SQLAlchemy session"""
    DBSession = sessionmaker(bind=ENGINE)
    return DBSession()
