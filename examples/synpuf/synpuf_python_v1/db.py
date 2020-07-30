import pyodbc
import pandas as pd


def get_data(database):
    cnxn = pyodbc.connect(
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=51.104.224.106,1433;"
        f"Database={database};"
        "UID=analysts;"
        "PWD=An8lysts."
    )

    df = pd.read_sql(
        "SELECT con.concept_name AS condition, gen.concept_name AS gender "
        "FROM condition_occurrence occ "
        "LEFT JOIN WEEK_00.dbo.concept con ON occ.condition_concept_id=con.concept_id "
        "LEFT JOIN person per ON occ.person_id=per.person_id "
        "LEFT JOIN WEEK_00.dbo.concept gen ON per.gender_concept_id=gen.concept_id;",
        cnxn,
    )

    return df
