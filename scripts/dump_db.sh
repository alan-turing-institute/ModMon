#!/usr/bin/env bash
DB="ModMon"

psql -d $DB -Atc "SELECT tablename from pg_tables;"|\
  while read TBL; do
    psql -c "COPY $TBL TO STDOUT WITH CSV" $DB > "dump/$TBL.csv"
  done
