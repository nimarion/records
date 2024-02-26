import requests
import pandas as pd


def determine_environment(row):
    if 'recordEvent' in row and row['recordEvent'] == "indoor":
        return "Indoor"
    if row['result'].endswith('i'):
        return "Indoor"
    return "Outdoor"


def isTechnical(discipline):
    return discipline[0].isdigit() == False and discipline[0] != "O"


def performance_to_float(performance):
    performance = performance.strip().replace(",", ".")
    if ":" in performance:
        # Running disciplines with format "1:23.45" or "1:23" or "2:29:08"
        parts = performance.split(":")
        if len(parts) != 2:
            return 0
        if "." in parts[1]:
            sub_parts = parts[1].split(".")
            minutes = int(parts[0])
            seconds = int(sub_parts[0])
            milliseconds = int(sub_parts[1])
            return (minutes * 60 + seconds) * 1000 + milliseconds
        return int(parts[0]) * 60 + int(parts[1])
    else:
        # Technical disciplines and sprint disciplines with format "10.23", "1.70"
        try:
            converted_performance = float(performance)
        except ValueError:
            return 0
        return int(converted_performance * 1000)


def getRecords(sex, indoor=False):
    url = f'https://www.tilastopaja.eu/api/records/area/{sex}?&indoor=all'
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
        disciplineDf['sex'] = sex
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

    df['result'] = df['result'].astype(str)
    df['Performance'] = df['result'].apply(performance_to_float)
    df["date"] = pd.to_datetime(df["date"], format='%Y-%m-%d')

    technical_rows = df[df['discipline'].apply(isTechnical)]
    non_technical_rows = df[~df['discipline'].apply(isTechnical)]

    technical_rows = technical_rows.sort_values(
        ['discipline', 'area', 'Performance'], ascending=[True, True, False])
    technical_rows = technical_rows.groupby(['area', 'discipline']).apply(
        lambda x: x[x['Performance'] == x['Performance'].max()]).reset_index(drop=True)
    non_technical_rows = non_technical_rows.sort_values(
        ['discipline', 'area', 'Performance'], ascending=[True, True, True])
    non_technical_rows = non_technical_rows.groupby(['area', 'discipline']).apply(
        lambda x: x[x['Performance'] == x['Performance'].min()]).reset_index(drop=True)

    df = pd.concat([technical_rows, non_technical_rows])

    df = df.sort_values(['discipline', 'area', 'date'],
                        ascending=[True, True, True])

    df = df.drop(columns=['Performance'])

    return df


menOutdoorRecords = getRecords('men', False)
womenOutdoorRecords = getRecords('women', False)
menIndoorRecords = getRecords('men', True)
womenIndoorRecords = getRecords('women', True)

df = pd.concat([menOutdoorRecords, womenOutdoorRecords,
               menIndoorRecords, womenIndoorRecords])
df.to_csv('arearecords/arearecords.csv', index=False)
menOutdoorRecords.to_csv('arearecords/menOutdoorRecords.csv', index=False)
womenOutdoorRecords.to_csv('arearecords/womenOutdoorRecords.csv', index=False)
menIndoorRecords.to_csv('arearecords/menIndoorRecords.csv', index=False)
womenIndoorRecords.to_csv('arearecords/womenIndoorRecords.csv', index=False)
