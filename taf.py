import pandas as pd
import argparse
import pathlib
import os

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '--input', help='Input file or folder', required=True)
    argparser.add_argument(
        '--output', help='Output file', required=True)
    argparser.add_argument(
        '--ignore', help='Ignore files', required=False, default=["taf.csv"])
    args = argparser.parse_args()

    disciplineMapping = pd.read_csv("mapping/disciplines.csv").astype(str)
    areaMapping = pd.read_csv("mapping/areas.csv").astype(str)

    files = []

    if not os.path.isfile(args.input):
        folder_path = pathlib.Path(args.input)
        files = folder_path.rglob("*.csv")
    else:
        files.append(args.input)

    outputDf = pd.DataFrame()
    for file in files:
        if os.path.basename(file) in args.ignore:
            continue
        df = pd.read_csv(file).astype(str)
        arearecordFile = 'type' in df.columns and df['type'].str.contains(
            'AR').any()
        worldrecordFile = 'type' in df.columns and df['type'].str.contains(
            'WR').any()
        nationrecordFile = 'type' in df.columns and df['type'].str.contains(
            'NR').any()
        arealeadFile = 'type' in df.columns and df['type'].str.contains(
            'AL').any()
        worldleadFile = 'type' in df.columns and df['type'].str.contains(
            'WL').any()
        nationleadFile = 'type' in df.columns and df['type'].str.contains(
            'NL').any()
        leadFile = arealeadFile or worldleadFile or nationleadFile

        df["discipline"] = df["discipline"].astype(str)

        # map discipline to taf
        if arearecordFile or worldrecordFile:
            mapping = disciplineMapping[["tilastopaja_wr_ar", "taf"]]
            mapping.columns = ["discipline", "taf"]
            df = pd.merge(df, mapping, on="discipline", how="left")
        elif nationrecordFile:
            mapping = disciplineMapping[["tilastopaja_nr", "taf"]]
            mapping.columns = ["discipline", "taf"]
            mapping["discipline"] = mapping["discipline"].astype(str)
            df = pd.merge(df, mapping, on="discipline", how="left")
        elif leadFile:
            mapping = disciplineMapping[["worldathletics_ranking", "taf"]]
            mapping.columns = ["discipline", "taf"]
            df = pd.merge(df, mapping, on="discipline", how="left")

        df = df.drop(columns=["discipline"])
        df = df.rename(columns={"taf": "discipline"})
        df = df.dropna(subset=["discipline"])

        df = df.rename(columns={"type": "code"})

        # map area to taf
        if arearecordFile or arealeadFile:
            df["Country"] = df["nation"]
            df = pd.merge(df, areaMapping, on="Country", how="left")
            df = df.drop(columns=["area", "Country"], errors="ignore")
            df = df.rename(columns={"AreaId": "type"})

        if nationleadFile:
            df["type"] = df["nation"]

        df = df.fillna("")
        df = df.replace("nan", "")

        if leadFile:
            df = df[df["rank"] == "1"]
            df = df.drop(columns=["rank", "region"], errors="ignore")

        outputDf = pd.concat([outputDf, df])

    outputDf['class'] = outputDf['sex'].apply(lambda x: 'M' if x == 'Male' else ('W' if x == 'Female' else 'X'))

    desired_order = ['code', 'type', 'discipline', 'class', 'result', 'wind', 'venue', 'venueCountry', 'environment', 'date', 'name', 'firstname', 'lastname', 'nation', 'yearOfBirth', 'sex']
    columns_to_drop = set(df.columns) - set(desired_order)
    outputDf = outputDf.drop(columns=columns_to_drop, errors="ignore")

    outputDf = outputDf.reindex(columns=desired_order)

    outputDf.to_csv(args.output, index=False, sep=';', encoding='ansi')
