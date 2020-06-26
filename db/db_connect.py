import pyodbc
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from schema import Base

PORT = "5432"
DB = "ModMon"

def get_connection():
    """Get a pyodbc connection that can be used to excecute queries"""
    # This is the driver location that Homebrew saves on Mac
    driver = "/usr/local/lib/psqlodbcw.so"
    return pyodbc.connect("DRIVER={" + driver + "};SERVER=localhost," + PORT + ";DATABASE=" + DB + ";Trusted_Connection=yes;")


def get_unique_id(table, column):
    """Get value one higher than the highest value in a SQL table column"""
    cnxn = get_connection()
    cursor = cnxn.cursor()
    cursor.execute("select max(" + column + ") from " + table)
    max_question_id = cursor.fetchone()[0]
    cnxn.close()
    if max_question_id:
        return max_question_id + 1
    return 1


def get_session():
    """Get SQLAlchemy session"""
    Base.metadata.bind = create_engine("postgresql://localhost:" + PORT + "/" + DB)
    DBSession = sessionmaker()
    return DBSession()
