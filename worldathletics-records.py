import pandas as pd
import requests
import argparse
import io

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
            records['sex'] = "Female"
        elif i == 1:
            records['sex'] = "Male"
        elif i == 2:
            records["sex"] == "Mixed"
        else:
            print(f"Unknown table with index {i}")
            continue
        df = pd.concat([df, records], ignore_index=True)    
    return df

if __name__ == '__main__':
    argparse = argparse.ArgumentParser()
    argparse.add_argument('--output', type=str, help='Output file', required=True)	
    argparse.add_argument('--category', type=str, help='URL to fetch data', required=True,
                           choices=['world-records', 'world-best-performances', 'world-u20-records', 'u18-world-best-performances', 'world-championships-in-athletics-records',
                                    'world-indoor-championships-records', 'world-u20-championships-records', 'world-u18-championships-records',
                                    'world-athletics-road-running-championships-records', 'world-half-marathon-championships-records', 'world-athletics-relays-records',
                                    'world-championships-combined-best-performances', 'combined-best-performances', 'olympic-games-records', 'youth-olympic-games-records'])
    argparse.add_argument('--type', type=str, help='WRU20,WLU20,...', required=True)
                                                                                                    
    args = argparse.parse_args()

    df = getRecords(args.category)
    df['type'] = args.type
    df.to_csv(args.output, index=False)