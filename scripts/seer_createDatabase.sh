#!/bin/sh

psql -h localhost -f seer_createDatabase.sql -U postgres
psql -h localhost -d seer -f seer_1975_create.sql -U postgres
psql -h localhost -d seer -f seer_1992_create.sql -U postgres
psql -h localhost -d seer -f seer_copyData.sql -U postgres
