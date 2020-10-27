#!/bin/bash

# Copy database config to example model directories
cp db_config.json synpuf_R/
cp db_config.json synpuf_python_v1/
cp db_config.json synpuf_python_v2/
cp db_config.json synpuf_stats/

# Setup modmon database and add example models
modmon_db_create
modmon_model_setup synpuf_R/ --nocheck
modmon_model_setup synpuf_python_v1/ --nocheck
modmon_model_setup synpuf_python_v2/ --nocheck --keepold
modmon_model_setup synpuf_stats/ --nocheck

# Run models on all databases
modmon_score --database 'WEEK_01'
modmon_score --database 'WEEK_02'
modmon_score --database 'WEEK_03'
modmon_score --database 'WEEK_04'
modmon_score --database 'WEEK_05'
modmon_score --database 'WEEK_06'
modmon_score --database 'WEEK_07'
modmon_score --database 'WEEK_08'
modmon_score --database 'WEEK_09'
modmon_score --database 'WEEK_10'
