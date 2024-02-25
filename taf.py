import pathlib
import pandas as pd

if __name__ == '__main__':
    folder_path = pathlib.Path("data")
    csv_files = folder_path.rglob("*.csv")

    tafDisciplines = pd.read_csv("disciplines.csv")

    taf_df = pd.DataFrame()

    # loop through tafDisciplines
    for index, row in tafDisciplines.iterrows():
        tafDiscipline = row['taf']
        tilastopajaDiscipline = row['tilastopaja']

        for s in ["women", "men"]:
            filename = f"data/{s}/{tilastopajaDiscipline}.csv"

            if not pathlib.Path(filename).exists():
                continue
                
            df = pd.read_csv(filename)
            df["event"] = tafDiscipline;
            df["class"] = "M" if s == "men" else "W"
            df["sex"] = "Male" if s == "men" else "Female"

            taf_df = pd.concat([taf_df, df])


    taf_df.to_csv("taf.csv", index=False)

            