#!/bin/bash
modmon_db_create
modmon_model_setup /Users/echalstrey/projects/DECOVID-dataaccess/monitor/examples/synpuf_stats/
modmon_model_setup /Users/echalstrey/projects/DECOVID-dataaccess/monitor/examples/synpuf_R/

modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_01'
modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_02'
modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_03'
modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_04'
modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_05'
modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_06'
modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_07'
modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_08'
modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_09'
modmon_run --start_date 2020-01-01 --end_date 2020-07-01 --database 'WEEK_10'
