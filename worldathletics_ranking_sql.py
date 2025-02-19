import pandas as pd
import argparse
import pathlib
import os
import sqlalchemy
import uuid
from datetime import datetime

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '--database-url', help='The URL of the database to connect to', required=True)
    argparser.add_argument(
        '--input', help='Input file or folder', required=True)
    args = argparser.parse_args()
    database_url = args.database_url

    files = []
    if not os.path.isfile(args.input):
        folder_path = pathlib.Path(args.input)
        files = folder_path.rglob("*.csv")
    else:
        files.append(args.input)

    files = [f for f in files if not "taf.csv" in str(f)]

    df = pd.DataFrame()

    for file in files:
        df = pd.concat([df, pd.read_csv(file)])

    disciplineMapping = pd.read_csv("mapping/disciplines.csv").astype(str)
    mapping = disciplineMapping[['worldathletics_ranking', "worldathletics"]]
    mapping.columns = ["Discipline", "worldathletics"]
    mapping["Discipline"] = mapping["Discipline"].astype(str)
    df["Discipline"] = df["Discipline"].astype(str)
    df = pd.merge(df, mapping, on="Discipline", how="left")
    df = df.drop(columns=["Discipline"])
    df = df.rename(columns={"worldathletics": "Discipline"})
    df = df.dropna(subset=["Discipline"])

    df['Sex'] = df['Sex'].apply(
        lambda x: 'M' if x == 'Male' else ('W' if x == 'Female' else 'X'))

    region_map = {
        'europe': 'EUR',
        'africa': 'AFR',
        'south america': 'SAM',
        'asia': 'ASI',
        'oceania': 'OCE',
        'north and central america': 'NAM',
    }

    df['Region'] = df['Region'].map(region_map).fillna(df['Region'])
    df['Region'] = df['Region'].apply(
        lambda x: x.upper() if pd.notnull(x) else x)

    db = sqlalchemy.create_engine(database_url)
    conn = db.connect()

    trans = conn.begin()

    try:
        table_exists_query = sqlalchemy.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'leads')"
        )
        result = conn.execute(table_exists_query).scalar()

        if result:
            delete_query = sqlalchemy.text(
             'DELETE FROM leads WHERE EXTRACT(YEAR FROM "Date") = :year')
            conn.execute(delete_query, {"year": datetime.now().year})

        df.insert(0, 'id', [str(uuid.uuid4()) for _ in range(len(df))])

        df.to_sql("leads", conn, if_exists="append", index=False, dtype={
            'Date': sqlalchemy.Date(),
            'Rank': sqlalchemy.Integer(),
            'Wind': sqlalchemy.Float(),
            'YOB': sqlalchemy.Integer(),
            'WorldathleticsId': sqlalchemy.Integer(),
            'id': sqlalchemy.String(36)})

        trans.commit()
    except Exception as e:
        trans.rollback()
        print(f"Error: {e}")
    finally:
        conn.close()
