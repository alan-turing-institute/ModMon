import argparse
from datetime import datetime
import pyodbc
import pandas as pd

#############
### Setup ###
#############

# Get the database name, start and end of date range to use for the model
parser = argparse.ArgumentParser()
parser.add_argument('db_name')
parser.add_argument('start_date', type=lambda s: datetime.strptime(s, '%Y-%m-%d'))
parser.add_argument('end_date', type=lambda s: datetime.strptime(s, '%Y-%m-%d'))
args = parser.parse_args()

# TODO: in the versioned SQL-Server implementation of the db, the dates will be used within the query(s) below
db_name = args.db_name # e.g. "synpuf"
# TODO: un-hardcode:
db_name = 'synpuf' # because run_models.py currently hardcoded to 'dummydb'
start_date = args.start_date # e.g. 2020-01-01
end_date = args.end_date # e.g. 2020-06-01

# Set up synpuf db connection
# TODO: modify this to be less specific to the local psql driver location
server = "localhost,5432"
driver = "/usr/local/lib/psqlodbcw.so" # This is the location Homebrew saves psql driver on Mac
cnxn = pyodbc.connect("DRIVER={" + driver + "};SERVER=" + server + ";DATABASE=" + db_name + ";Trusted_Connection=yes;")

#######################
### Calculate stuff ###
######################

person = pd.read_sql('SELECT * FROM person;', cnxn)

month_counts = person.groupby('month_of_birth').count().person_id

months = {'January': 1,
    	 'February': 2,
    	 'March': 3,
    	 'April': 4,
    	 'May': 5,
    	 'June': 6,
    	 'July': 7,
    	 'August': 8,
    	 'September': 9,
    	 'October': 10,
    	 'November': 11,
    	 'December': 12}

#########################################################
### Metrics (replace with actually interesting stats) ###
#########################################################

# Number of people born in January
jan_births = month_counts[months['January']]

# Number of people born in August
aug_births = month_counts[months['August']]

# Number of people born in 1983
year_counts = person.groupby('year_of_birth').count().person_id
born_83 = year_counts[1983]

# Create df of all metrics
metrics = pd.DataFrame([["jan_births", jan_births],
                        ["aug_births", aug_births],
                        ["born_83", born_83]],
                columns=["metric", "value"])

# Save the metrics to csv:
metrics.to_csv("metrics.csv",  index=False)
