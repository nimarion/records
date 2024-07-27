#!/bin/bash
exit 0
python worldathletics-records.py --type WR --output tmp/worldrecords/senior.csv --category world-records
python cleanup.py --input tmp/worldrecords/senior.csv
python taf.py --input tmp/worldrecords/senior.csv --output records/world.csv --mapping worldathletics_records --ageGroup senior