# import pyodbc
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from schema import Base
from sqlalchemy import func

PORT = "5432"
DB = "ModMon"


def get_unique_id(session, column):
    """Get value one higher than the highest value in a SQL table column,
    where the column should be the SQL alchemy table column, e.g. Dataset.datasetid"""
    max_id = session.query(func.max(column)).scalar()
    if max_id:
        return max_id + 1
    return 1


def get_session():
    """Get SQLAlchemy session"""
    Base.metadata.bind = create_engine("postgresql://localhost:" + PORT + "/" + DB)
    DBSession = sessionmaker()
    return DBSession()
