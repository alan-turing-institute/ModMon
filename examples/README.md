# Model examples for the DECOVID model appraisal system

This directory contains several example model folders that were used for testing the model appraisal system, all of which follow the format outlined in [monitor/docs/project_structure.md](../docs/project_structure.md).

- `wine-quality` models are trained on a [popular machine learning dataset](http://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/)
- `synpuf` models are trained on a dummy OMOP dataset called [synpuf](https://forums.ohdsi.org/t/synpuf/4936), for which the Turing REG team have set up multiple databases on a remote server, see below.

### Setup "Synpuf" dummy model appraisal dataset

For testing purposes, a script has been added that will set up a model monitoring database called `ModMon` and add results for the example models found in [monitor/examples/synpuf](../examples/synpuf), which use the dummy OMOP database "Synpuf".

If an existing ModMon db exists first run `modmon_delete` (see [monitor/docs/installation.md](../docs/installation.md)). Then navigate to the `monitor/examples/synpuf` directory and run:

```bash
> bash synpuf_modmon_db_setup.sh
```

⚠️ _NOTE 1: If you have installed ModMon in a conda environment you will need to have it activated before running this script - see [monitor/docs/model_monitoring_instructions.md](../docs/installation.md)._

⚠️ _NOTE 2: This will take quite a while to run, about 15 minutes._

Multiple instances of the Synpuf database have been set up on a remote server, that the models connect to. By changing the `--database` flag to one of `WEEK_01` through `WEEK_10`, different versions of the Synpuf data can be used by the models. This simulates the model appraisal scenario for DECOVID where the OMOP database is updated periodically with new patient data.

The configuration of the database server is stored in [synpuf/db_config.json](synpuf/db_config.json). This file is copied to all the example model directories as part of running [synpuf_modmon_db_setup.sh](synpuf/synpuf_modmon_db_setup.sh).


