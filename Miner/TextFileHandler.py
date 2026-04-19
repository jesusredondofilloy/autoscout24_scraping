import pandas as pd


class TextFileHandler:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None

    def load_data_txt(self, encoding='latin-1'):
        try:
            self.df = pd.read_csv(self.file_path, sep=';', encoding=encoding)
        except UnicodeDecodeError:
            print(f"Error: Unable to decode the file with encoding '{encoding}'.")

    def load_data_csv(self, dtype=None):
        self.df = pd.read_csv(self.file_path, dtype=dtype)

    def export_column(self, column_name):
        return self.df[column_name].astype(str).tolist()

    # kept for backwards compatibility
    def export_comune_column(self):
        return self.export_column('Comune')

    def export_capoluogo_column(self):
        return self.export_column('Capoluogo')
