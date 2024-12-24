#!/bin/bash
python worldathletics-records.py --type WRU20 --output tmp/u20worldrecords.csv --category world-u20-records
python cleanup.py --input tmp/u20worldrecords.csv
python taf.py --input tmp/u20worldrecords.csv --output records/world-u20.csv --mapping worldathletics_records --ageGroup JU20