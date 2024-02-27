import pandas as pd
import argparse
import pathlib
import os


def isTechnical(discipline):
    discipline = str(discipline)
    technical_disciplines = ["HJ", "PV", "LJ", "TJ", "SP",
                             "DT", "HT", "JT", "WT", "JTOLD", "Hep", "Dec", "One Hour"]
    if (discipline in technical_disciplines):
        return True
    non_technical_disciplines = ["Mile", "Mar", "HM"]
    if (discipline in non_technical_disciplines):
        return False
    return discipline[0].isdigit() == False and discipline[0] != "O"


def performance_to_float(performance):
    performance = performance.strip().replace(",", ".")
    if ":" in performance:
        # Running disciplines with format "1:23.45" or "1:23" or "2:29:08"
        parts = performance.split(":")
        if len(parts) < 2:
            print(f"Invalid performance: {performance}")
            return 0
        if "." in parts[1]:
            sub_parts = parts[1].split(".")
            minutes = int(parts[0])
            seconds = int(sub_parts[0])
            milliseconds = int(sub_parts[1])
            return (minutes * 60 + seconds) * 1000 + milliseconds
        if (len(parts) == 3):
            hours = int(parts[0])
            minutes = int(parts[1])
            if ("." in parts[2]):
                sub_parts = parts[2].split(".")
                seconds = int(sub_parts[0])
                milliseconds = int(sub_parts[1])
                return (hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds
            seconds = int(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        return int(parts[0]) * 60 + int(parts[1])
    else:
        # Technical disciplines and sprint disciplines with format "10.23", "1.70"
        try:
            converted_performance = float(performance)
        except ValueError:
            print(f"Invalid performance: {performance}")
            return 0
        return int(converted_performance * 1000)


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '--input', help='Input file or folder', required=True)
    args = argparser.parse_args()

    files = []
    # check if input is file or folder
    if not os.path.isfile(args.input):
        folder_path = pathlib.Path(args.input)
        files = folder_path.rglob("*.csv")
    else:
        files.append(args.input)

    files = [f for f in files if not "taf.csv" in str(f)]

    for file in files:
        df = pd.read_csv(file)
        outputDf = pd.DataFrame()

        df['result'] = df['result'].astype(str)
        df['result'] = df['result'].str.replace(r'[^0-9:.]', '', regex=True)
        # remove leading : from result if present
        df['result'] = df['result'].str.replace(r'^:', '', regex=True)
        df['Performance'] = df['result'].apply(performance_to_float)
        df["date"] = pd.to_datetime(df["date"], format='%Y-%m-%d')

        areaCleanup = 'area' in df.columns
        worldrecordCleanup = 'type' in df.columns and df['type'].str.contains(
            'WR').any()
        nationalrecordCleanup = 'type' in df.columns and df['type'].str.contains(
            'NR').any()

        for e in ["Outdoor", "Indoor"]:
            dfEnvironment = df[df['environment'] == e]
            for s in ["Male", "Female"]:
                dfSex = dfEnvironment[dfEnvironment['sex'] == s]
                technical_rows = dfSex[dfSex['discipline'].apply(
                    isTechnical)]
                non_technical_rows = dfSex[~dfSex['discipline'].apply(
                    isTechnical)]

                if not technical_rows.empty:
                    if areaCleanup:
                        technical_rows = technical_rows.sort_values(
                            ['discipline', 'area', 'Performance'], ascending=[True, True, False])
                        technical_rows = technical_rows.groupby(['area', 'discipline']).apply(
                            lambda x: x[x['Performance'] == x['Performance'].max()]).reset_index(drop=True)
                    elif worldrecordCleanup:
                        technical_rows = technical_rows.sort_values(
                            ['discipline', 'Performance'], ascending=[True, False])
                        technical_rows = technical_rows.groupby(['discipline']).apply(
                            lambda x: x[x['Performance'] == x['Performance'].max()]).reset_index(drop=True)
                    elif nationalrecordCleanup:
                        technical_rows = technical_rows.sort_values(
                            ['nation', 'Performance'], ascending=[True, False])
                        technical_rows = technical_rows.groupby('nation').apply(
                            lambda x: x[x['Performance'] == x['Performance'].max()]).reset_index(drop=True)

                if not non_technical_rows.empty:
                    if areaCleanup:
                        non_technical_rows = non_technical_rows.sort_values(
                            ['discipline', 'area', 'Performance'], ascending=[True, True, True])
                        non_technical_rows = non_technical_rows.groupby(['area', 'discipline']).apply(
                            lambda x: x[x['Performance'] == x['Performance'].min()]).reset_index(drop=True)
                    elif worldrecordCleanup:
                        non_technical_rows = non_technical_rows.sort_values(
                            ['discipline', 'Performance'], ascending=[True, True])
                        non_technical_rows = non_technical_rows.groupby(['discipline']).apply(
                            lambda x: x[x['Performance'] == x['Performance'].min()]).reset_index(drop=True)
                    elif nationalrecordCleanup:
                        non_technical_rows = non_technical_rows.sort_values(
                            ['nation', 'Performance'], ascending=[True, True])
                        non_technical_rows = non_technical_rows.groupby('nation').apply(
                            lambda x: x[x['Performance'] == x['Performance'].min()]).reset_index(drop=True)

                outputDf = pd.concat(
                    [outputDf, technical_rows, non_technical_rows])

        if areaCleanup:
            outputDf = outputDf.sort_values(
                ['sex', 'environment', 'discipline',  'area', 'date'], ascending=[False, False, True, True, True]
            )
        elif worldrecordCleanup:
            outputDf = outputDf.sort_values(
                ['sex', 'environment', 'discipline', 'date'], ascending=[False, False, True, True])
        elif nationalrecordCleanup:
            outputDf = outputDf.sort_values(
                ['environment', 'nation', 'date', 'name'], ascending=[False, True, True, True])

        outputDf = outputDf.drop(columns=['Performance'])

        outputDf.to_csv(file, index=False)
