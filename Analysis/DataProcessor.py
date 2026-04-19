import pandas as pd


class DataProcessor:
    def __init__(self, input_file):
        self.input_file = input_file

    def read_data(self):
        return pd.read_csv(self.input_file)

    def remove_duplicates(self, df):
        if 'guid' in df.columns and df['guid'].notna().any():
            return df.drop_duplicates(subset=['guid'], keep='first')
        columns_to_check = ['make', 'model', 'mileage', 'fuel-type', 'first-registration']
        return df.drop_duplicates(subset=columns_to_check, keep='first')

    def preprocess_data(self, df):
        df = df.copy()
        df.loc[df['first-registration'] == 'new', 'mileage'] = 0
        return df[df['mileage'] != 'unknown'].reset_index(drop=True)

    def round(self, df, by):
        df = df.copy()
        df['mileage'] = pd.to_numeric(df['mileage'], errors='coerce').fillna(0).astype(int)
        df['mileage_grouped'] = (df['mileage'] // by) * by
        return df

    def save_processed_data(self, df, output_file):
        df.to_csv(output_file, index=False)
        print("Modified data saved to", output_file)
