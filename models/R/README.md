# Dummy R Model

Largely inspired by this tutorial: http://www.sthda.com/english/articles/37-model-selection-essentials-in-r/153-penalized-regression-essentials-ridge-lasso-elastic-net/#loading-required-r-packages

2 scripts:
* `train.R`: Train a ridge regression model, save it as `model.rds`:
  - `Rscript train.R`
* `predict.R`: Calculate metrics for all rows between `start_idx` and `run_idx`, saves results as `metrics.json`.
  - `Rscript predict.R start_idx end_idx`
  
## Environment

Uses `renv` to share package versions etc., see docs here: https://rstudio.github.io/renv/articles/renv.html
* Initialise project (also scans current directory tree for dependencies): `renv::init()`
* Update environment specs if something changed: `renv::snapshot()`
* I believe `renv::init()` will create the environment for you if it doesn't exist (i.e. for sharing with someone else).