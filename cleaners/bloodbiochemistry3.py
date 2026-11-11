from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save
import re

RAW_FILE_NAME = "bloodbiochemistry_corrected_sep2026.xlsx"

df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME), sheet_name="Integrated_Data")
print(df)
print(df.columns)

unit_df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME), sheet_name="Metadata")

unit_dict = {}
for _, row in unit_df.iterrows():
    print(row)
    col = row["variable"].strip()

    if col in df.columns:
        if pd.isna(row["unit"]):
            continue
        unit = row["unit"].strip()
        if unit == "":
            continue
        unit_dict[col] = unit
    else:
        raise "Wrong column"


df = clean_site_column(df)

string_cols = ["patient", "visit", "site", "tbil", "crp", "sgot"]
float_cols = [s for s in df.columns if s not in string_cols]
df = change_types(df, string_cols=string_cols, float_cols=float_cols)

test_data_frame(df)

metadata = DataFrameMetadata(df, "3.1", comment="Blood biochemistry", categorical_features=["visit", "site"],
                             column_units=unit_dict)

save(metadata, "bloodbiochemistry")

print(df.columns)
print(df.dtypes)
print(df)
