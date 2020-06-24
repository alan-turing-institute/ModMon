# Setup db

1. Nagigate to `monitor/db` dir
1. Install required python packages: `pip install -r requirements.txt`
1. Create db: `createdb ModMon "DECOVID Model Monitoring"`
2. Create tables: `psql -f schema.sql ModMon`
3. Connect to db: `psql -h localhost -p 5432 ModMon`

# Connect with psqlodbc

1. Install driver for ODBC for PostgreSQL: `brew install psqlodbc`
2. Connect to database with Python (see test_connection.py)

# SQLAlchemy

1. Create schema (if changes to schema.sql): `sqlacodegen postgresql://username@localhost:5432/ModMon --outfile schema.py`

# Model Monitoring

## Set up a new model

1. Navigate to validation scripts
    ```bash
    cd path/to/validation_scripts
    ```
2. Where `model` is the folder submitted by the analyst:
    ```bash
    python model_setup.py path/to/model
    ```
3. Running this for the first time imports reference results/metrics from when the analyst ran their model on test data (`metrics.csv`):
    ```bash
    python import_model_results.py path/to/model
    ```

## Log a new result for a model

1. Log in to the db and choose a model: `psql -h localhost -p 5432 ModMon`, then:
    ```SQL
    select name, modelID from models; -- choose a model (note the modelID number)
    ```
    ```SQL
    select modelVersion from modelVersions where modelID=<modelID>; -- list model versions (note one of them)
    ```
    ```SQL
    select location from modelVersions where modelID=<modelID> and modelVersion='<modelVersion>'; -- gets `path/to/model`
    ```
2. Now you know the location, set up the environment:
    ```bash
    cd path/to/model
    ```
	For **Python** projects:
    ```bash
    conda env create -f environment.yml
    ```
    ```bash
    conda activate <model name>
    ```
	For **R** projects, open an R cli (`R`):
    ```R
	renv::init()
	renv::snapshot()
    ```
3. Find, then run the analyst's designated command to run their model on new data (substitute new args), creating a new `metrics.csv`:
    ```SQL
    select command from modelVersions where modelID=<modelID> and modelVersion='<modelVersion>';
    ```
	For example:
    ```bash
    python run_model.py <db name> <start date (yyyy-mm-dd)> <end date (yyyy-mm-dd)>
    ```
4. Back to validation scripts:
    ```bash
    cd path/to/validation_scripts
    ```
5. Log the new prediction metrics in results table, designating as not a reference result:
    ```bash
    python import_model_results.py path/to/model
    ```
