# Model examples for the DECOVID model appraisal system

This directory contains several example model folders that were used for testing the model appraisal system (see `monitor/docs/model_monitoring_instructions.md` for more details on how the system works).

- `wine-quality` models are trained on a [popular machine learning dataset](http://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/)
- `synpuf` models are trained on a dummy OMOP dataset called [synpuf](https://forums.ohdsi.org/t/synpuf/4936), for which the Turing REG team have set up multiple databases on a remote server, see below.

### Setup "Synpuf" dummy model appraisal dataset

For testing purposes, a script has been added that will set up a model monitoring database called `ModMon` and add results for the example models found in `monitor/examples/synpuf` which use the dummy OMOP database "Synpuf". If an existing ModMon db exists first run `modmon_delete` (see `monitor/docs/model_monitoring_instructions.md`). Navigate to the `monitor/examples/synpuf` dir and run:

```bash
> bash synpuf_modmon_db_setup.sh
```

Multiple instances of this database have been set up on a remote server, that the models connect to. By changing the `--database` flag to one of `WEEK_01` through `WEEK_10`, different versions of the Synpuf data can be used by the models. This simulates the model appraisal scenario for DECOVID where the OMOP database is updated periodically with new patient data.

*NOTE: You will need to have activated the ModMon environment and installed ModMon to run this script - see `monitor/docs/model_monitoring_instructions.md`.*
