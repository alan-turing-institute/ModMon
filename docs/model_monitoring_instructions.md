# Model Monitoring Instructions

## Pre-requisites

* conda: [Linux](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html), [Mac](https://docs.conda.io/projects/conda/en/latest/user-guide/install/macos.html)
* PostgreSQL: [Linux](https://www.postgresql.org/download/linux/), [Mac](https://wiki.postgresql.org/wiki/Homebrew)

## Conda Environment

We recommend running ModMon in a virtual environment, such as a conda environment. To create one:
```bash
> conda create -n ModMon -y python=3.8
```
Then activate the environment with:
```bash
> conda activate ModMon
```
⚠️ **_All steps in this document should then be run with the `ModMon` environment activated._**

## Install ModMon

Navigate to the `monitor` directory and then run:
```bash
> pip install -e .
```
The `-e` flag above installs the package in editable mode (**used for development only**)

## Setup ModMon Database

To create the ModMon database run:
```bash
> modmon_db_create
```

To check the database exists and is functioning normally run:
```bash
> modmon_db_check
```
This should print a list of tables and columns. Or you can connect directly to the database with the psql command line tool:
```basH
> psql -h localhost -p 5432 ModMon
```

## Model Monitoring

### Set up a new model

1. To check the code, environments, metadata and metrics files of a model are in the expected formats you can run the command:
   ```bash
   > modmon_model_check path/to/model
   ```
   Where `path/to/model` is the path to the directory to be submitted to the database. This command runs general sanity checks
   of the metadata, database and metrics. You can optionally pass the argument `--create_envs` as well to test that any defined
   virtual environments can be created sucessfully.

2. **_TODO:_** Verify reproducibility

3. Add a new model to the database:
    ```bash
    > modmon_model_setup path/to/model
    ```
    Where `path/to/model` is the absolute path to the directory submitted by the analyst.

### Verify reproducibility

1. Verify reproducibility with `repro-catalogue` (see [docs](https://repro-catalogue.readthedocs.io/en/latest/example_use.html#run-analysis)) - Firstly we log the reference results (we don't expect to monitor code and data changes with repro-catalogue here):
    ```bash
    > cd path/to/model
    > catalogue engage --input_data data --code code
    > catalogue disengage --input_data data --code code --output_data results
    ```
2. Run the analyst model code (see the `metadata.json` or `modelVersions.command` in the db) **_TODO_**: Automate this part
3. Repeat step 1
4. Compare the result files before and after you ran the analyst code run by model monitoring code:
    ```bash
    > catalogue compare <TIMESTAMP1>.json <TIMESTAMP2>.json
    ```

### Log a new result for all models

1. Run this command, replacing `<start_date>` and `<end_date>` with appropriate values (in `Y-m-d` format):
   ```bash
   > modmon_run --start_date <start_date> --end_date <end_date>
   ```

2. New metric values for all active model versions will be added to the results table in the monitorinig database.

### Schedule Automated Model Runs

**_TODO_**

### Visualise model reults

**_TODO_**
