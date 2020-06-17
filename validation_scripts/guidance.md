# Analyst guidance

## Files

### Simple python example

```
|-- model
|  |-- environment.yml             <- Required: Sets up environment needed for model to run
|  |-- run_model.py                <- Required: Metrics calculation script (language of choice e.g. run_model.R)
|  |-- model.sav                   <- Optional: file ext. of choice (alternately don't include this and run_model.py also trains model)
|  |-- metadata.json                <- Required: Manually compiled
|  |-- metrics.csv                 <- Required: Output of analyst run of run_model.py
|  |-- training_metrics.csv        <- Optional: Output of your model training

```

This is one example, but only the metrics calculation script (`run_model.py` or whichever name and language you choose) and `metrics.csv` are essential. If the script also trains the model, instead of loading a pre-trained model, that's fine.

## File templates

Template for `metrics.csv` and `training_metrics.csv`. Must have a metric and a value column.

|metric|value|
| ---  | --- |
| mse  | 0.1 |
| r2   | 0.9 |
...

Template `metadata.json`:

```JSON
{
	"team": "REG",
	"contact": "Ed Chalstrey",
	"contact_email": "echalstrey@turing.ac.uk",
	"team_description": "A team from The Alan Turing Institute",
	"research_question": "Investigate wine quality dataset",
	"model_name": "WineQuality1",
	"model_description": "Model to assess wine quality",
	"model_version": "1.0.0",
	"db_name": "dummydb",
	"data_window_start": "03/03/2020",
	"data_window_end": "03/06/2020",
	"model_train_datetime": "03/06/2020",
	"training_data_description": "This is 50% of the wine quality dataset",
	"model_run_datetime": "11/07/2020",
	"test_data_description": "This is the 50% of the wine quality dataset that was not used for training the model",
	"command": "python run_prediction_model.py <db name> <start date (yyyy-mm-dd)> <end date (yyyy-mm-dd)>"
}
```

# Validator guidance

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
    ```bash
conda env create -f environment.yml
    ```
    ```bash
conda activate <model name>
    ```
3. Find, then run the analyst's designated command to run their model on new data (substitute new args), creating a new `metrics.csv`:
    ```SQL
select command from modelVersions where modelID=<modelID> and modelVersion='<modelVersion>';
    ```

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
