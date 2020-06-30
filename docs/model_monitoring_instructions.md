# Model Monitoring Instructions

## Pre-requisites

* conda: [Linux](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html), [Mac](https://docs.conda.io/projects/conda/en/latest/user-guide/install/macos.html)
* PostgreSQL: [Linux](https://www.postgresql.org/download/linux/), [Mac](https://wiki.postgresql.org/wiki/Homebrew)

## Setup ModMon Environment

1. Navigate to the `monitor` directory
2. Create the `ModMon` conda environment: `conda create env`
3. Activate the environment: `conda activate ModMon`

⚠️ **_All steps below should be performed with the `ModMon` environment activated._**

## Setup database

1. Navigate to the `monitor/db` directory.
2. Create the database: `python db_create.py`
3. Test database connection: `python db_connect.py` should print a list of tables and columns, or you can connect directly to the database from the command line with `psql -h localhost -p 5432 ModMon`.

## Model Monitoring

### Set up a new model

1. Navigate to the `monitor/db` directory.

2. **_TODO:_** Verify reproducibility

3. Add a new model to the database:
    ```bash
    python model_setup.py path/to/model
    ```
    Where `path/to/model` is the absolute path to the directory submitted by the analyst.

### Log a new result for all models

1. Navigate to the `monitor/db` directory.

2. Run this script, replacing `<start_date>` and `<end_date>` with appropriate values (in `Y-m-d` format):
   ```bash
   python run_models.py --start_date <start_date> --end_date <end_date>
   ```

3. New metric values for all active model versions will be added to the results table in the monitorinig database.

### Schedule Automated Model Runs

**_TODO_**

### Visualise model reults

**_TODO_**
