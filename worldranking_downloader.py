import pandas as pd
from datetime import datetime
import os

df = pd.read_csv('mapping/disciplines.csv')
df = df[df['worldathletics_ranking'].notnull()]

for index, row in df.iterrows():
    discipline = row['worldathletics_ranking']
    type = row['worldathletics_ranking_type']
    year = datetime.now().year

    sex = ["men", "women"]
    if(discipline == "4x400-metres-relay"):
        sex.append("mixed")
    
    for sex in sex:
        os.system(f"python worldranking.py --type {type} --discipline {discipline} --sex {sex} --ageCategory senior --year {year} --regionType world --output leads/world/{sex}-{discipline}.csv")
        #os.system(f"python worldranking.py --type {type} --discipline {discipline} --sex {sex} --ageCategory senior --year {year} --regionType area --region europe --output leads/area/europe/{sex}-{discipline}.csv")
        #os.system(f"python worldranking.py --type {type} --discipline {discipline} --sex {sex} --ageCategory senior --year {year} --regionType area --region africa --output leads/area/africa/{sex}-{discipline}.csv")
        #os.system(f"python worldranking.py --type {type} --discipline {discipline} --sex {sex} --ageCategory senior --year {year} --regionType area --region asia --output leads/area/asia/{sex}-{discipline}.csv")
        #os.system(f"python worldranking.py --type {type} --discipline {discipline} --sex {sex} --ageCategory senior --year {year} --regionType area --region \"north and central america\" --output leads/area/naca/{sex}-{discipline}.csv")
        #os.system(f"python worldranking.py --type {type} --discipline {discipline} --sex {sex} --ageCategory senior --year {year} --regionType area --region oceania --output leads/area/oceania/{sex}-{discipline}.csv")
        #os.system(f"python worldranking.py --type {type} --discipline {discipline} --sex {sex} --ageCategory senior --year {year} --regionType area --region \"south america\" --output leads/area/sa/{sex}-{discipline}.csv")
        os.system(f"python worldranking.py --type {type} --discipline {discipline} --sex {sex} --ageCategory senior --year {year} --regionType countries --region ger --output leads/country/ger/{sex}-{discipline}.csv") 