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
    argparser.add_argument('--mapping', help='Mapping column', required=True)
    argparser.add_argument('--ageGroup', help='Age group', choices=['senior', "JU20", "JU18"], required=True)
    args = argparser.parse_args()

    disciplineMapping = pd.read_csv("mapping/disciplines.csv").astype(str)
    areaMapping = pd.read_csv("mapping/areas.csv").astype(str)
    mappingColumn = args.mapping

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
        arearecordFile = 'Record Type' in df.columns and df['Record Type'].str.contains(
            'AR').any()
        worldrecordFile = 'Record Type' in df.columns and df['Record Type'].str.contains(
            'WR').any()
        nationalrecordFile = 'Record Type' in df.columns and df['Record Type'].str.contains(
            'NR').any()
        arealeadFile = 'Record Type' in df.columns and df['Record Type'].str.contains(
            'AL').any()
        worldleadFile = 'Record Type' in df.columns and df['Record Type'].str.contains(
            'WL').any()
        nationalleadFile = 'Record Type' in df.columns and df['Record Type'].str.contains(
            'NL').any()
        leadFile = arealeadFile or worldleadFile or nationalleadFile


        # Map discipline to taf discipline code
        mapping = disciplineMapping[[mappingColumn, "taf"]]
        mapping.columns = ["Discipline", "taf"]
        mapping["Discipline"] = mapping["Discipline"].astype(str)
        df["Discipline"] = df["Discipline"].astype(str)
        df = pd.merge(df, mapping, on="Discipline", how="left")
        df = df.drop(columns=["Discipline"])
        df = df.rename(columns={"taf": "Discipline"})
        df = df.dropna(subset=["Discipline"])

        # Rename record type to code
        df = df.rename(columns={"Record Type": "Code"})

        # Map area to taf area code
        if arearecordFile or arealeadFile:
            df["Country"] = df["Nat"]
            df = pd.merge(df, areaMapping, on="Country", how="left")
            df = df.drop(columns=["area", "Country"], errors="ignore")
            df = df.rename(columns={"AreaId": "Type"})
            df["Type"] = df["Type"].fillna(0)

        # Bei nationalen Rekorden und Bestleistungen wird die Nation als Typ verwendet 
        # damit die Rekorde nur für Athleten aus dem eigenen Land angezeigt werden
        if nationalleadFile or nationalrecordFile:
            df["Type"] = df["Nat"]

        df = df.fillna("")
        df = df.replace("nan", "")

        # Bei Bestleistungen wird nur der erste Eintrag verwendet
        if leadFile:
            if "Rank" in df.columns:
                df = df[df["Rank"] == "1"]
            df = df.drop(columns=["Rank", "Region"], errors="ignore")

        outputDf = pd.concat([outputDf, df])

    outputDf['Class'] = outputDf['Sex'].apply(lambda x: 'M' if x == 'Male' else ('W' if x == 'Female' else 'X'))

    # Für Jugendklassen wird entsprechend der Suffix angehängt z.B. JU20 oder JU18
    if(args.ageGroup != 'senior'):
        outputDf['Class'] = outputDf['Class'] + args.ageGroup

    if 'YOB' in outputDf.columns:
        outputDf['YOB'] = outputDf['YOB'].fillna('').astype(str) 
        outputDf['YOB'] = outputDf['YOB'].replace('', '-1') 
        outputDf['YOB'] = outputDf['YOB'].astype(float).astype(int) 
        outputDf['YOB'] = outputDf['YOB'].replace(-1, "") 
    
    # Vorname und Nachname werden aus dem vollen in "Name" beim ersten Leerzeichen getrennt
    # "YOB" überprüfung da Staffeln kein "YOB" haben
    if 'Name' in outputDf.columns and 'YOB' in outputDf.columns:
        print("Splitting name")
        outputDf[['Firstname', 'Lastname']] = outputDf['Name'].str.split(
            pat=' ', n=1, expand=True)
        outputDf['Lastname'] = outputDf['Lastname'].str.lower().str.title()
    
    # Spaltenreihenfolge anpassen und unnötige Spalten entfernen
    desired_order = ['Code', 'Type', 'Discipline', 'Class', 'Result', 'Wind', 'Venue', 'Venue Country', 'Environment', 'Date', 'Firstname', 'Lastname', 'Nat', 'YOB', 'Sex', 'WorldathleticsId']
    columns_to_drop = set(df.columns) - set(desired_order)
    outputDf = outputDf.drop(columns=columns_to_drop, errors="ignore")

    outputDf = outputDf.reindex(columns=desired_order)

    output_dir = os.path.dirname(args.output)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    
    outputDf = outputDf.rename({"Nat": "Nation"})

    outputDf.to_csv(args.output, index=False, sep=';')
