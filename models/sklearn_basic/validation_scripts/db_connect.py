import pyodbc
import pandas as pd


def get_connection():
    server = "localhost,5432"
    db_name = "ModMon"
    # This is the driver location that Homebrew saves on Mac
    driver = "/usr/local/lib/psqlodbcw.so"
    return pyodbc.connect("DRIVER={" + driver + "};SERVER=" + server + ";DATABASE=" + db_name + ";Trusted_Connection=yes;")
