#!/bin/bash
python worldathletics-records.py --type AR --output tmp/arearecords/senior/africa.csv --category african-records
python worldathletics-records.py --type AR --output tmp/arearecords/senior/asia.csv --category asian-records
python worldathletics-records.py --type AR --output tmp/arearecords/senior/europe.csv --category european-records
python worldathletics-records.py --type AR --output tmp/arearecords/senior/nacac.csv --category nacac-records
python worldathletics-records.py --type AR --output tmp/arearecords/senior/oceanian.csv --category oceanian-records
python worldathletics-records.py --type AR --output tmp/arearecords/senior/southamerica.csv --category south-american-records
python cleanup.py --input tmp/arearecords/senior
python taf.py --input tmp/arearecords/senior --output records/area.csv --mapping worldathletics_records --ageGroup senior