import pandas as pd
import requests
import argparse
import io
import re


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

def getRecords(category):
    url = f'https://worldathletics.org/records/by-category/{category}'
    response = requests.get(url)
    tables = pd.read_html(io.StringIO(str(response.text)))
    if(len(tables) == 0):
        return None

    df = pd.DataFrame()
   
    for i, table in enumerate(tables):
        records = table
        if i == 0:
            records['Sex'] = "Female"
        elif i == 1:
            records['Sex'] = "Male"
        elif i == 2:
            records['Sex'] = "Mixed"
        else:
            print(f"Unknown table with index {i}")
            continue    
        
        df = pd.concat([df, records], ignore_index=True)

    if 'DOB' in df.columns:
        df[['Firstname', 'Lastname']] = df['Competitor'].str.split(
            pat=' ', n=1, expand=True)
        df['Lastname'] = df['Lastname'].str.lower().str.title()
        df['Name'] = df['Firstname'] + ' ' + df['Lastname']
        df.drop(columns=['Firstname', 'Lastname'], inplace=True, errors='ignore')
        df['DOB'] = pd.to_datetime(
            df['DOB'], format='%d %b %Y', errors='coerce')
        df["YOB"] = df['DOB'].dt.year
        df['YOB'] = df['YOB'].fillna('').astype(str) 
        df['YOB'] = df['YOB'].replace('', '-1') 
        df['YOB'] = df['YOB'].astype(float).astype(int) 

    df["environment"] = df["Venue"].apply(
        lambda x: "Indoor" if "(i)" in x else "Outdoor")

    df[['venueCountry', 'venue', 'stadium']] = df['Venue'].apply(parse_venue)

    # remove state from venue eg New York BY or Eugene OR
    df['venue'] = df['venue'].str.replace(r' ([A-Z]+)$', '', regex=True)
    # eg from Stockholm/G to Stockholm, Göteborg/U to Göteborg 
    df['venue'] = df['venue'].str.replace(r'/.*$', '', regex=True)
    df['venue'] = df['venue'].str.replace(r',$', '', regex=True)
    df['Date'] = pd.to_datetime(df['Date'], format='%d %b %Y')

    df.rename(columns={'Perf': 'Result'}, inplace=True, errors='ignore')
    df = df.drop(columns=['DOB', 'stadium', 'Perf', 'Venue', 'Competitor', 'Progression'], errors='ignore')    
    df.rename(columns={ 'Country': 'Nation', 'environment': 'Environment', 'venue': 'Venue', 'venueCountry': 'Venue Country'}, inplace=True, errors='ignore')

    # Pending ratification
    df = df[~df['Result'].str.contains(r'\*')]

    return df

if __name__ == '__main__':
    argparse = argparse.ArgumentParser()
    argparse.add_argument('--output', type=str, help='Output file', required=True)	
    argparse.add_argument('--category', type=str, help='URL to fetch data', required=True,
                           choices=['world-records', 'world-best-performances', 'world-u20-records', 'u18-world-best-performances', 'world-championships-in-athletics-records',
                                    'world-indoor-championships-records', 'world-u20-championships-records', 'world-u18-championships-records',
                                    'world-athletics-road-running-championships-records', 'world-half-marathon-championships-records', 'world-athletics-relays-records',
                                    'world-championships-combined-best-performances', 'combined-best-performances', 'olympic-games-records', 'youth-olympic-games-records', 'world-u20-leading-2024'])
    argparse.add_argument('--type', type=str, help='WRU20,WLU20,...', required=True)
                                                                                                    
    args = argparse.parse_args()

    df = getRecords(args.category)
    df['Type'] = args.type
    df.to_csv(args.output, index=False)