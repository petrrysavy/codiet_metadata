from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save

### MASS SPECTROMETRY - serum

RAW_FILE_NAME = "ms_aminoacids_serum_CICbioGUNE_20250130.xlsx"

df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME))
print(df)
print(df.columns)

df = column_names_remove_spaces(df)
df = column_names_remove_underscores(df)
df.columns = df.columns.str.replace("--", "-", regex=True)

df[['patient', 'visit']] = df['sample-id'].str.rsplit('-', n=1, expand=True)
df = df.drop(columns=["sample-id"])
df = column_names_to_lowercase(df)

#TODO are empty cells truly zeroes
df.replace([""], 0.0)

print(df.columns)
string_cols = ["patient", "visit", "type", "sample-type"]
float_cols = [s for s in df.columns if s not in string_cols]
df = change_types(df, string_cols=string_cols, float_cols=float_cols)

df = df[string_cols + [col for col in df.columns if col not in string_cols]]

test_data_frame(df)

metadata = DataFrameMetadata(df, "1.3", comment="Mass spectrometry - serum", categorical_features=["visit", "type"])

save(metadata, "ms-serum")

print(df.columns)
print(df)
