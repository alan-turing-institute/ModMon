import pyodbc
import pandas as pd


def get_connection():
    """Get a pyodbc connection that can be used to excecute queries"""
    server = "localhost,5432"
    db_name = "ModMon"
    # This is the driver location that Homebrew saves on Mac
    driver = "/usr/local/lib/psqlodbcw.so"
    return pyodbc.connect("DRIVER={" + driver + "};SERVER=" + server + ";DATABASE=" + db_name + ";Trusted_Connection=yes;")


def get_unique_id(cursor, table, column):
    """Get value one higher than the highest value in a SQL table"""
    cursor.execute("select max(" + column + ") from " + table)
    max_question_id = cursor.fetchone()[0]
    if max_question_id:
        return max_question_id + 1
    else:
        return 1
