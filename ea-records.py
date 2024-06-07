import pandas as pd
import re
import argparse
from bs4 import BeautifulSoup

def parse_venue(venue):
    venue = venue.strip()
    parts = venue.split(', ')

    if len(parts) == 1:
        city, country = parse_country_and_city(parts[0])
        return pd.Series({'country': country, 'city': city, 'stadium': None})

    stadium = parts[0]
    rest = ', '.join(parts[1:])
    city, country = parse_country_and_city(rest)

    return pd.Series({'country': country, 'city': city, 'stadium': stadium})

def parse_country_and_city(country_and_city):
    regex = re.compile(r'(.+?)\s*\((\w+(?:\s+\w+)*)\)')
    match_result = regex.match(country_and_city)

    if not match_result:
        raise ValueError(
            f"Cannot parse country and city from {country_and_city}")

    city = match_result.group(1)
    country = match_result.group(2)

    return city, country

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--input', help='HTML file', required=True)
    argparser.add_argument('--output', help='Output CSV file', required=True)
    argparser.add_argument('--recordType', help='Record Type', required=True)
    argparser.add_argument(
        '--sex', choices=["Male", "Female", "Mixed"], required=True)
    args = argparser.parse_args()

    rows = []
    with open(args.input, 'r', encoding='utf-8', errors='ignore') as f_in:
        soup = BeautifulSoup(f_in.read(), 'html.parser')
        for row in soup.find_all('div', class_='ea-table-row'):
            row_data = []
            for field in row.find_all('div', class_='ea-table-field'):
                title = field.find(
                    'div', class_='mobile-field-title').text.strip()
                value = field.find(
                    'div', class_='mobile-field-content').text.strip()
                if (title == "Discipline"):
                    row_data.append({"Discipline": value})
                elif (title == "Perf."):
                    row_data.append({"Performance": value})
                elif (title == "Wind"):
                    row_data.append({"Wind": value})
                elif (title == "Competitor"):
                    row_data.append({"Competitor": value})
                elif (title == "DOB"):
                    row_data.append({"DOB": value})
                elif (title == "Nat."):
                    row_data.append({"Nation": value})
                elif (title == "Venue"):
                    row_data.append({"Venue": value})
                elif (title == "Date"):
                    row_data.append({"Date": value})

            rows.append({k: v for d in row_data for k, v in d.items()})

    df = pd.DataFrame(rows)
    df["Record Type"] = args.recordType
    df["Sex"] = args.sex
    df['Date'] = pd.to_datetime(df['Date'], format='%d %b %Y')
    df = df.rename(columns={"Discipline": "Discipline",
                   "Performance": "Result", "Wind": "Wind", "Competitor": "Name"})
    df = df[~df["Discipline"].str.contains("\✱")]  # ratification
    df = df[~df["Result"].str.contains("ℹ")] 
    df["Environment"] = df["Venue"].apply(
        lambda x: "Indoor" if "(i)" in x else "Outdoor")   
   
    df["Name"] = df.apply(lambda row: "" if row["DOB"].strip() == "" else row["Name"], axis=1) # Relay
    df[['Firstname', 'Lastname']] = df.apply(lambda row: pd.Series(row['Name'].split(' ', 1)) if row['Name'] else pd.Series([None, None]), axis=1)
    df['Lastname'] = df['Lastname'].str.lower().str.title()

    # remove Short Track from discipline
    df['Discipline'] = df['Discipline'].str.replace(r' Short Track$', '', regex=True)
    
    # filter all where venue is not empty
    df = df[df["Venue"] != ""]
    df[['Venue Country', 'Venue', 'Stadium']] = df['Venue'].apply(parse_venue)
    df.drop(columns=['Stadium', 'Name'], inplace=True)

    df.to_csv(args.output, index=False)
