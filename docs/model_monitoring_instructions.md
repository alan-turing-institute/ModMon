# Model Monitoring Instructions

## Pre-requisites

* conda: [Linux](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html), [Mac](https://docs.conda.io/projects/conda/en/latest/user-guide/install/macos.html)
* PostgreSQL: [Linux](https://www.postgresql.org/download/linux/), [Mac](https://wiki.postgresql.org/wiki/Homebrew)
* Git: [link](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

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

## Configure ModMon

To configure database and some environoment settings ModMon uses a configuration file in
.ini format. By default this is the file in `modmon/config/defaults.ini`. This defines:
* The ModMon database to be a postgresql database on localhost, without a username and password.
* conda environments to install dependencies via the internet.
* R models to be run in a conda environment with the R version specified by the renv.lock file.
* Submitted models to be stored in the user's home directory at `$HOME/modmon/storage`.

To change the default values you should copy `modmon/config/defaults.ini` to the file
`$HOME/.modmon.ini`, where `$HOME` is the path to your home directory.

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

### Check a model before submission

To check the code, environments, metadata and metrics files of a model are in the expected formats you can run the command:
```bash
> modmon_model_check path/to/model
```
Where `path/to/model` is the path to the directory to be submitted to the database. This command runs general sanity checks
of the metadata, database and metrics. To perform a more substantial check you can also pass the arguments:
- `--create_envs` to test that any defined virtual environments can be created successfully.
- `--repro_check` to verify that the command can be run successfully and the same metrics values are reproduced. The reproducibility
  check on `metrics.csv` is done with `repro-catalogue` (see [docs](https://repro-catalogue.readthedocs.io/en/latest/example_use.html#run-analysis)) - in this case the virtual env will be created even if the `--create_envs` flag is not used.

### Set up a new model

To add a new model to the database:
```bash
> modmon_model_setup path/to/model
```
Where `path/to/model` is the absolute path to the directory submitted by the analyst.

By default `modmon_model_setup` initially runs pre-submission checks (see above) and asks the user whether they want to continue with the setup based on the results of those checks. There are several arguments that can be used to configure this behaviour, to see these run `modmon_model_setup --help` from the command-line, which should give you something like this:
```
usage: modmon_model_setup [-h] [--nocheck] [--quickcheck] [--noconfirm] [--force] model

Add a model version to the ModMon monitoring system.

positional arguments:
  model         Path to model directory to add

optional arguments:
  -h, --help    show this help message and exit
  --nocheck     If set, setup model without performing pre-submission checks
  --quickcheck  If set, don't perform environment or reproducibility checks
  --noconfirm   If set, don't ask for user confirmation after checks
  --force       If set, setup model even if checks fail
```

### Log a new result for all models

1. Run this command, replacing `<start_date>` and `<end_date>` with appropriate values (in `Y-m-d` format),
   and `<database>` with the name of the database to connect to:
   ```bash
   > modmon_run --start_date <start_date> --end_date <end_date> --database <database>
   ```

2. New metric values for all active model versions will be added to the results table in the monitorinig database.

### Schedule Automated Model Runs

**_TODO_**

### Visualise model reults

**_TODO_**

### Delete All ModMon Data

If you wish to delete everything created or stored by ModMon and start with a new system you can run:
```bash
> modmon_delete
```
**This cannot be undone!** It will delete:
- The database
- All models in storage
- All ModMon related conda environments.