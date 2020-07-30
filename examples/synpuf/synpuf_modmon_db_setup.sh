#!/bin/bash
modmon_db_create
modmon_model_setup synpuf_stats/
modmon_model_setup synpuf_R/
modmon_model_setup synpuf_python_v1/
modmon_model_setup synpuf_python_v2/

modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_01' --run_inactive
modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_02' --run_inactive
modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_03' --run_inactive
modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_04' --run_inactive
modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_05' --run_inactive
modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_06' --run_inactive
modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_07' --run_inactive
modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_08' --run_inactive
modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_09' --run_inactive
modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_10' --run_inactive
