import argparse
from datetime import datetime
import pyodbc
import pandas as pd
import psycopg2
import numpy as np


def get_birthdate(year, month, day):
    birthdate = pd.to_datetime(
        (year * 10000 + month * 100 + day).apply(str), format="%Y%m%d",
    )
    return birthdate


def compute_age(start_date, end_date):
    age = np.floor(end_date.subtract(start_date).dt.days / 365.25).astype("int")
    return age


#############
### Setup ###
#############

# Get the database name, start and end of date range to use for the model
parser = argparse.ArgumentParser()
parser.add_argument("db_name")
parser.add_argument("start_date", type=lambda s: datetime.strptime(s, "%Y-%m-%d"))
parser.add_argument("end_date", type=lambda s: datetime.strptime(s, "%Y-%m-%d"))
args = parser.parse_args()

# TODO: in the versioned SQL-Server implementation of the db, the dates will be used within the query(s) below
db_name = args.db_name  # e.g. "synpuf"
start_date = args.start_date  # e.g. 2020-01-01
end_date = args.end_date  # e.g. 2020-06-01

# Set up synpuf db connection
# TODO: save this info in a config file
server = "51.104.224.106,1433"
driver = "/usr/local/lib/libmsodbcsql.17.dylib"  # This is the location Homebrew saves SQL-Server driver on Mac
uid = "analysts"
pwd = "An8lysts."
cnxn = pyodbc.connect(
    "DRIVER={" + driver + "};" +
    "SERVER=" + server + ";" +
    "DATABASE=" + db_name + ";" +
    "UID=" + uid + ";" +
    "PWD=" + pwd
)

#######################
### Calculate stuff ###
######################

person = pd.read_sql("SELECT * FROM person;", cnxn)

month_counts = person.groupby("month_of_birth").count().person_id

months = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

#######################
### Population Size ###
#######################

population_size = pd.read_sql("SELECT COUNT(person_id) AS count FROM person", cnxn)["count"][0]

################################
###     Patient Mortality    ###
################################

"""Patient Mortality"""
death_number = pd.read_sql(
    "SELECT COUNT(person_id) AS count \
            FROM observation_period op \
            WHERE op.person_id \
                IN (SELECT person_id FROM death)",
    cnxn,
)

mortality = death_number["count"][0] / population_size * 100

################################
###  Average Onset Duration  ###
################################

"""Mean duration in days from admission to first condition onset"""
obs_cdn_table = pd.read_sql(
    "SELECT op.observation_period_start_date,\
                    ce.condition_era_start_date,\
                    op.person_id \
                FROM observation_period op \
                LEFT JOIN condition_era ce \
                    ON ce.person_id = op.person_id ",
    cnxn,
)
# remove patients without any condition throughout the observation
obs_cdn_table.dropna(inplace=True)
# sort DataFrame by condition start day
obs_cdn_table.sort_values(by=["condition_era_start_date"], inplace=True, ascending=True)
# only select the first occurrance of condition (earliest condition) for each patient
obs_cdn_table.drop_duplicates(subset=["person_id"], inplace=True)
obs_cdn_table["duration"] = (
    obs_cdn_table["condition_era_start_date"]
    - obs_cdn_table["observation_period_start_date"]
)

avg_onset = obs_cdn_table.duration.mean().days


#########################################################
### Metrics (replace with actually interesting stats) ###
#########################################################

# Number of people born in January
jan_births = month_counts[months["January"]]

# Number of people born in August
aug_births = month_counts[months["August"]]

# Number of people born in 1983
year_counts = person.groupby("year_of_birth").count().person_id
born_60 = year_counts[1960]

# Create df of all metrics
metrics = pd.DataFrame(
    [
        ["jan_births", jan_births],
        ["aug_births", aug_births],
        ["born_60", born_60],
        ["population_size", population_size],
        ["mortality", mortality],
        ["average_onset_duration", avg_onset],
    ],
    columns=["metric", "value"],
)

# Save the metrics to csv:
metrics.to_csv("metrics.csv", index=False)

print(metrics)
