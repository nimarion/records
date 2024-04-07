import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
import argparse

def download_parse():
    response = requests.get("https://worldathletics.org/records/competition-performance-rankings")
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', class_='records-table')
    if (table == None):
        return None
    df = pd.read_html(io.StringIO(str(table)))[0]
    df = df.dropna(axis=1, how='all')

    return df

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--output", help="output file", default="competition_ranking.csv")
    args = argparser.parse_args()
    
    df = download_parse()

    df.to_csv(args.output, index=False)
