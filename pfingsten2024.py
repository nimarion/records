import pandas as pd

df = pd.read_csv('taf.csv')

women = ["100", "400", "800", "1500", "400H", "SPE", "KUG", "HOC"]

men = ["100", "400", "800", "1500", "400H",
       "SPE", "KUG", "HOC", "3KH", "STA", "5K0"]

men_df = df[(df['event'].isin(men)) & (df['class'] == 'M')]
women_df = df[(df['event'].isin(women)) & (df['class'] == 'W')]

df = pd.concat([men_df, women_df])

df.to_csv('pfingsten2024.csv', index=False)
df.to_excel('pfingsten2024.xlsx', index=False)