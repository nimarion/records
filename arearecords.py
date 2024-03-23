import requests
import pandas as pd


def determine_environment(row):
    if 'recordEvent' in row and row['recordEvent'] == "indoor":
        return "Indoor"
    if row['result'].endswith('i'):
        return "Indoor"
    return "Outdoor"

def getRecords(sex, indoor=False):
    url = f'https://www.tilastopaja.info/api/records/area/{sex}?&indoor=all'
    response = requests.get(url)
    json = response.json()
    if (json['templates'] is None):
        return None

    df = pd.DataFrame()
    records = json['templates'][0]["divs"]
    for record in records:
        discipline = record["title"]
        record = record["tables"][0]["body"]
        disciplineDf = pd.DataFrame(record)
        disciplineDf['discipline'] = discipline
        disciplineDf['sex'] = "Male" if sex == "men" else "Female"
        df = pd.concat([df, disciplineDf])

    df = df.rename(columns={'rowTitle': 'area', 'country': 'nation'})
    df['environment'] = df.apply(determine_environment, axis=1)

    if indoor:
        df = df[df['environment'] == "Indoor"]
    else:
        df = df[df['environment'] == "Outdoor"]

    df['result'] = df['result'].str.replace(r'[^0-9:.]', '', regex=True)
    desired_columns = ['result', 'discipline', 'area', 'wind', 'nation', 'venue',
                       'venueCountry', 'date', 'name', 'yearOfBirth', 'sex', 'event', 'type', 'environment']

    valid_columns = []

    for col in desired_columns:
        if col in df.columns:
            valid_columns.append(col)
    df = df[valid_columns]
    
    return df


menOutdoorRecords = getRecords('men', False)
womenOutdoorRecords = getRecords('women', False)
menIndoorRecords = getRecords('men', True)
womenIndoorRecords = getRecords('women', True)

df = pd.concat([menOutdoorRecords, womenOutdoorRecords,
               menIndoorRecords, womenIndoorRecords])

df["type"] = "AR"

df.to_csv('arearecords/arearecords.csv', index=False)
