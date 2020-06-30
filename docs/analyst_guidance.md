# Analyst guidance

## Files

### Simple python example

```
|-- model
|  |-- environment.yml             <- Required: Sets up environment needed for model to run
|  |-- run_model.py                <- Required: Metrics calculation script (language of choice e.g. run_model.R)
|  |-- model.sav                   <- Optional: file ext. of choice (alternately don't include this and run_model.py also trains model)
|  |-- metadata.json               <- Required: Manually compiled
|  |-- metrics.csv                 <- Required: Output of analyst run of run_model.py
|  |-- training_metrics.csv        <- Optional: Output of your model training

```

This is one example, but only the metrics calculation script (`run_model.py` or whichever name and language you choose) and `metrics.csv` are essential. If the script also trains the model, instead of loading a pre-trained model, that's fine.

## File templates

### Metrics Files

Template for `metrics.csv` and `training_metrics.csv`. Must have a metric and a value column.

|metric|value|
| ---  | --- |
| mse  | 0.1 |
| r2   | 0.9 |
...

### Metadata Files

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
	"command": "python run_prediction_model.py <database> <start_date> <end_date>"
}
```

- **command:** Must contain the placeholders `<database>`, `<start_date>` and `<end_date>` (case sensitive but in any order). In automated runs of your model these will be replaced by:

  - `<database>`: The OMOP database the monitoring system has access to.
  - `<start_date>`: The date of the earliest row to extract from the database (`Y-m-d` format)
  - `<end_date>`: The date of the latest row to extract from the database (`Y-m-d` format)

  Your script must use these inputs to connect to the given database, and to modify any database queries to return only data updated between the given start and end date.

- **`<data_window_start>` and `<data_window_end>`:** The date range used to produce the values in the `metrics.csv` file you provide. Running your specified command with `<data_window_start>` as `<start_date>` and `<data_window_end>` as `<end_date>` should exactly reproduce the values in `metrics.csv`. This will be tested before adding a model to the monitoring system.