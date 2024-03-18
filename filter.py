import pandas as pd
import argparse

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '--input', help='Input taf file', required=True)
    argparser.add_argument(
        '--output', help='Output taf file', required=True)
    argparser.add_argument("--disciplines", help="Disciplines filter file", required=True)
    args = argparser.parse_args()

    input_data = pd.read_csv(args.input).astype(str)
    disciplines = pd.read_csv(args.disciplines).astype(str)

    input_data['discipline_sex'] = input_data['discipline'] + '_' + input_data['sex']
    disciplines['discipline_sex'] = disciplines['discipline'] + '_' + disciplines['sex']

    unique_discipline_sex = disciplines['discipline_sex'].unique()
    filtered_input = input_data[input_data['discipline_sex'].isin(unique_discipline_sex)]

    filtered_input = filtered_input.drop(columns=['discipline_sex'])

    filtered_input = filtered_input.fillna("")
    filtered_input = filtered_input.replace("nan", "")

    # yearOfBirth as int
    if 'yearOfBirth' in filtered_input.columns:
        filtered_input['yearOfBirth'] = filtered_input['yearOfBirth'].astype(float).astype(int)

    filtered_input.to_csv(args.output, index=False, sep=';')