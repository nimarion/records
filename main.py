import requests
import pandas as pd
import os

def getEvents(sex):
    url = f'https://www.tilastopaja.eu/api/inputs/events/nationalrecords/senior/{sex}'
    response = requests.get(url)
    json = response.json()
    data = json["data"]
    return [x["value"] for x in data]

def determine_environment(row):
    if 'rowTitle' in row and row['rowTitle'] == "indoor":
        return "Indoor"
    if row['result'].endswith('i'):
        return "Indoor"
    return "Outdoor"

def isTechnical(discipline):
    technical_disciplines = ["HJ", "PV", "LJ", "TJ", "SP", "DT", "HT", "JT"]
    for prefix in technical_disciplines:
        if discipline.startswith(prefix):
            return True
    return False

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

def getRecords(sex, event):
    url = f'https://www.tilastopaja.eu/api/nationalrecords/world/{sex}?indoor=all&event={event}'
    response = requests.get(url)
    json = response.json()
    if (json['templates'] is None):
        return None
    records = json['templates'][0]["divs"][0]["tables"][0]["body"]
    df = pd.DataFrame(records)

    df = df.rename(columns={'country': 'nation'})
    # add event column
    df['event'] = event
    df['sex'] = "Male" if sex == "men" else "Female"
    df['type'] = "NR"
    df['environment'] = df.apply(determine_environment, axis=1)
    # remove all non numeric characters from result epext , :
    df['result'] = df['result'].str.replace(r'[^0-9:.]', '', regex=True)

    # only keep rows result, nation, venue, venueCountry, date, name, yearOfBirth, sex, event, type, environment
    desired_columns = ['result', 'nation', 'venue', 'venueCountry', 'date', 'name', 'yearOfBirth', 'sex', 'event', 'type', 'environment']

    valid_columns = []

    for col in desired_columns:
        if col in df.columns:
            valid_columns.append(col)

    return df[valid_columns]

def saveRecords(df, output):
    output_dir = os.path.dirname(output)
    discipline = os.path.basename(output).split(".")[0]
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    df = df[df['environment'] != 'Indoor']
    df = df.drop(columns=['environment'])

    df = df.sort_values('date', ascending=True).drop_duplicates(subset=['result', 'name', 'nation'], keep='first')
    df = df.sort_values('nation')

    df['result'] = df['result'].astype(str)
    df['Performance'] = df['result'].apply(performance_to_float)

    if isTechnical(discipline):
        df = df.sort_values(['nation', 'Performance'], ascending=[True, False]) 
        df = df.groupby('nation').apply(lambda x: x[x['Performance'] == x['Performance'].max()]).reset_index(drop=True)
    else:
        df = df.sort_values(['nation', 'Performance'], ascending=[True, True])
        df = df.groupby('nation').apply(lambda x: x[x['Performance'] == x['Performance'].min()]).reset_index(drop=True)

    df = df.drop(columns=['Performance'])    

    if df.empty:
        if os.path.exists(output):
            os.remove(output)
        return

    df.to_csv(output, index=False)

if __name__ == '__main__':
    for sex in ["men", "women"]:
        events = getEvents(sex)

        for event in events:
            print(f'Getting records for {event}')
            records = getRecords(sex, event)
            if records is not None:
                saveRecords(records, f'./data/{sex}/{event}.csv')
            else:
                print(f'No records found for {event}')
