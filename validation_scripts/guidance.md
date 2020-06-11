# Analyst guidance

## Files

```
|-- model
|  |-- Makefile                       <- Sets up environment and contains cmd for run_model.py
|  |-- model.sav                      <- file ext. of choice
|  |-- run_model.py                   <- Takes model.sav as arg (language of choice e.g. run_model.R)
|  |-- data
|  |-- |-- metadata.csv               <- Manually compiled
|  |-- |-- training_metrics.csv       <- Output of your model training
|  |-- |-- prediction_metrics.csv     <- Output of analyst run of run_model.py

```

## File templates

Template for `prediction_metrics.csv` and `training_metrics.csv`. Must have a metric and a value column.

|metric|value|
| ---  | --- |
| mse  | 0.1 |
| r2   | 0.9 |
...

Template `metadata.csv`. Must have a Field and a Value column.

|Field | Field Required | Value|
| --- | --- | --- |
|team | TRUE | REG|
|contact | TRUE | Ed Chalstrey|
|contact_email | TRUE | echalstrey@turing.ac.uk|
|team_description | FALSE | A team from The Alan Turing Institute|
|research_question | TRUE | Investigate wine quality dataset|
|model_name | TRUE | WineQuality1|
|model_description | FALSE | Model to assess wine quality|
|model_version | TRUE | 1.0.0|

# Validator guidance

## Set up a new model

1. `python model_setup.py model` <- where `model` is the folder submitted by the analyst
2. `python import_model_results model` <- running this for the first time imports reference results/metrics from when the analyst ran their model on test data (`prediction_metrics.csv`)

## Log a new result for a model

1. `Make` <- set up the environment (perhaps also does step 2 below)
1. `python run_model.py` (or R equivalent) <- creates a new `prediction_metrics.csv`
2. `python import_model_results model` <- the new prediction metrics logged in results table, designated as not a reference result
