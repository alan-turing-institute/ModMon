import pyodbc
import pandas as pd

server = "localhost,5432"
db_name = "ModMon"
# This is the driver location that Homebrew saves on Mac
driver = "/usr/local/lib/psqlodbcw.so"

cnxn = pyodbc.connect("DRIVER={" + driver + "};SERVER=" + server + ";DATABASE=" + db_name + ";Trusted_Connection=yes;")

df = pd.read_sql("SELECT * FROM information_schema.tables;", cnxn)
print(df.head(3))
