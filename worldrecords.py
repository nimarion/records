import requests
import pandas as pd

def determine_environment(row):
    if 'rowTitle' in row and row['rowTitle'] == "indoor":
        return "Indoor"
    if row['result'].endswith('i'):
        return "Indoor"
    return "Outdoor"

def getRecords(sex, indoor=False):
    url = f'https://www.tilastopaja.eu/api/records/world/{sex}?&indoor=all'
    response = requests.get(url)
    json = response.json()
    if (json['templates'] is None):
        return None

    df = pd.DataFrame()
    records = json['templates'][0]["divs"]
    for record in records:
        record = record["tables"][0]["body"]
        disciplineDf = pd.DataFrame(record)
        disciplineDf['sex'] = "Male" if sex == "men" else "Female"
        df = pd.concat([df, disciplineDf])

    df = df.rename(columns={'recordEvent': 'discipline', 'country': 'nation'})
    df['environment'] = df.apply(determine_environment, axis=1)

    if indoor:
        df = df[df['environment'] == "Indoor"]
    else:
        df = df[df['environment'] == "Outdoor"]

    desired_columns = ['result', 'discipline', 'wind', 'nation', 'venue', 'venueCountry',
                       'date', 'name', 'yearOfBirth', 'sex', 'event', 'type', 'environment']

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

df["type"] = "WR"

df.to_csv('worldrecords/worldrecords.csv', index=False)