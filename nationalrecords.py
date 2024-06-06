import requests
import pandas as pd
import os

def getDisciplines(sex):
    url = f'https://www.tilastopaja.info/api/inputs/events/nationalrecords/senior/{sex}'
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

def getRecords(sex, discipline):
    url = f'https://www.tilastopaja.info/api/nationalrecords/world/{sex}?indoor=all&event={discipline}'
    response = requests.get(url)
    json = response.json()
    if (json['templates'] is None):
        return None
    records = json['templates'][0]["divs"][0]["tables"][0]["body"]
    df = pd.DataFrame(records)

    df = df.rename(columns={'country': 'nation'})

    df['discipline'] = discipline
    df['sex'] = "Male" if sex == "men" else "Female"
    df['Record Type'] = "NR"
    df['environment'] = df.apply(determine_environment, axis=1)
    
    desired_columns = ['result', 'wind', 'nation', 'venue', 'venueCountry', 'date', 'name', 'yearOfBirth', 'sex', 'discipline', 'Record Type', 'environment']

    valid_columns = []

    for col in desired_columns:
        if col in df.columns:
            valid_columns.append(col)

    return df[valid_columns]

def saveRecords(df, output):
    output_dir = os.path.dirname(output)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    df = df.sort_values('Date', ascending=True).drop_duplicates(subset=['Result', 'Name', 'Nation'], keep='first')
    df = df.sort_values('Nation')

    df.to_csv(output, index=False)

if __name__ == '__main__':
    for sex in ["men", "women"]:
        disciplines = getDisciplines(sex)

        for discipline in disciplines:
            print(f'Getting records for {discipline}')
            records = getRecords(sex, discipline)
            if records is not None:
                records = records.rename(columns={'result': 'Result', 'venue': 'Venue', 'venueCountry': 'Venue Country',
                            'date': 'Date', 'name': 'Name', 'yearOfBirth': 'YOB', 'sex': 'Sex', 'environment': 'Environment', 'discipline': 'Discipline', 'wind': 'Wind', 'nation': 'Nation'})
                saveRecords(records, f'./tmp/nationalrecords/{sex}/{discipline}.csv')
            else:
                print(f'No records found for {discipline}')
