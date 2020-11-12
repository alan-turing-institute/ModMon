#!/bin/sh

psql -h localhost -f seer_createDatabase.sql -U postgres

for fn in 1975 1992
do
  # CREATE TABLE
  psql -h localhost -d seer -f seer_${fn}_create.sql -U postgres
  # REPLACE SPACES WITH UNDERSCORES
  sed -i '1s/ /_/g' seer_${fn}_breastCancer.csv
  # USE FIRST 20 LINES TO GENERATE CREATE STATEMENT
  head -n 20 seer_${fn}_breastCancer.csv |csvsql > seer_${fn}_create.sql
  # SUBSTITUTE stdin WITH seer????
  sed -i 's/stdin/seer1975/' seer_${fn}_create.sql
  # REMOVE NOT NULLs
  sed -i 's/NOT NULL//g' seer_${fn}_create.sql
  # SUBSTITUTE Blank(s) WITH NULL
  sed -i 's/Blank(s)/NULL/g' seer_${fn}_breastCancer.csv
  # REMOVE QUOTES
  sed -i 's/"NULL"/NULL/g' seer_${fn}_breastCancer.csv
  # SUBSTITUTE Unknown WITH NULL
  sed -i 's/,Unknown,/,NULL,/g' seer_${fn}_breastCancer.csv
  # SUBSTITUTE "Unknown" WITH NULL
  sed -i 's/,"Unknown",/,NULL,/g' seer_${fn}_breastCancer.csv
done

psql -h localhost -d seer -f seer_copyData.sql -U postgres
