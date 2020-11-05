#!/bin/sh

head -n 20 ../2020-10-22/seer_1975_breastCancer.csv |csvsql > seer_1975_create.sql
head -n 20 ../2020-10-22/seer_1992_breastCancer.csv |csvsql > seer_1992_create.sql
