import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
import argparse
import os
import re
import sys
import urllib.parse

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


def get_url_params(ageCategory, regionType, region, limitByCountry):
    url_params = f'?regionType={regionType}&ageCategory={ageCategory}'
    if region and ' ' in region and regionType != 'world':
        region = urllib.parse.quote(region)
    if region != None and regionType != 'world':
        url_params += f'&region={region}'
    if limitByCountry != None:
        url_params += f'&maxResultsByCountry={limitByCountry}'
    return url_params


def get_url(type, discipline, sex, ageCategory, year, regionType, region, limitByCountry=None):
    url = f'https://worldathletics.org/records/toplists/{type}/{discipline}/all/{sex}/{ageCategory}/{year}'
    url += get_url_params(ageCategory, regionType, region, limitByCountry)
    return url


def download_parse(url, discipline, sex, regionType, region):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', class_='records-table')
    if (table == None):
        return None
    df = pd.read_html(io.StringIO(str(table)))[0]
    df = df.dropna(axis=1, how='all')
    df["Discipline"] = discipline
    if sex == "mixed":
        df["Sex"] = "Mixed"
    elif sex == "men":
        df["Sex"] = "Male"
    else:
        df["Sex"] = "Female"

    df['Date'] = pd.to_datetime(df['Date'], format='%d %b %Y')
    if regionType == "countries":
        df["Record Type"] = "NL"
    elif regionType == "area":
        df["Record Type"] = "AL"
    elif regionType == "world":
        df["Record Type"] = "WL"

    # Staffeln haben kein DOB
    if 'DOB' in df.columns:
        df['DOB'] = pd.to_datetime(
            df['DOB'], format='%d %b %Y', errors='coerce')
        df["YOB"] = df['DOB'].dt.year

    if (region != None):
        df["Region"] = region

    df[['Country', 'City', 'Stadium']] = df['Venue'].apply(parse_venue)

    df["Environment"] = df["Venue"].apply(
        lambda x: "Indoor" if "(i)" in x else "Outdoor")

    df = df.drop(columns=['Results Score',
                 'RegionType', 'DOB', 'Pos'], errors='ignore')
    
    name_links = {}

    for row in table.find_all('tr'):
        name_tag = row.find('a', href=True)  # Find the first <a> tag
        if name_tag and name_tag.text.strip() in df['Competitor'].values:
            match = re.search(r'\d+',  name_tag['href'])
            if match:
                name_links[name_tag.text.strip()] = match.group()

    df['WorldathleticsId'] = df['Competitor'].map(name_links)

    df = df.rename(columns={
                   'City': 'Venue City', 'Country': 'Venue Country', 'Mark': 'Result', 'Nat': 'Nation', 'WIND': 'Wind', 'Competitor': 'Name'})

    df['Venue'] = df['Venue'].apply(lambda x: x.split(' (', 1)[0])
    df['Venue'] = df['Venue'].apply(lambda x: x.split(', ', 1)[0])
    df['Venue'] = df['Venue'].apply(lambda x: x.strip())

    return df


if __name__ == "__main__":
    argparse = argparse.ArgumentParser()
    argparse.add_argument("--type", help="Type of discipline",  choices=[
                          "sprints", "middlelong", "jumps", "throws", "road-running", "race-walks", "hurdles", "relays"], required=True)
    argparse.add_argument("--discipline", help="Discipline", required=True)
    argparse.add_argument(
        "--sex", choices=["women", "men", "mixed"], required=True)
    argparse.add_argument(
        "--ageCategory", choices=["u18", "u20", "senior", "all"], required=True)
    argparse.add_argument("--year", help="Year", required=True)
    argparse.add_argument(
        "--regionType", choices=["world", "area", "countries"], default="world")
    argparse.add_argument("--region", help="Region", required=False)
    argparse.add_argument("--output", help="Output file", required=False)
    argparse.add_argument("--limitByCountry", help="Limit by country",
                          required=False, choices=[1, 2, 3, 4, 5], type=int)

    args = argparse.parse_args()

    if args.regionType in ["area", "country"] and args.region is None:
        argparse.error(
            "--region is required when --regionType is 'area' or 'country'")

    type = args.type
    discipline = args.discipline
    sex = args.sex
    ageCategory = args.ageCategory
    year = args.year
    regionType = args.regionType
    region = args.region
    limitByCountry = args.limitByCountry

    url = get_url(type, discipline, sex, ageCategory,
                  year, regionType, region, limitByCountry)
    print(url)

    df = download_parse(url, discipline, sex, regionType, region)

    if df is None:
        print("No data found")
        sys.exit(1)

    if args.output:
        output_dir = os.path.dirname(args.output)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        df.to_csv(args.output, index=False)
