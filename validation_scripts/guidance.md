# How to submit a model

# Files

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
