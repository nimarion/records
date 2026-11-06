#!/bin/bash
set -e
python nationalrecords.py
python cleanup.py --input tmp/nationalrecords
python taf.py --input tmp/nationalrecords --output records/national.csv --mapping tilastopaja_nr --ageGroup senior
