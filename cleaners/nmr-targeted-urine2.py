from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save

### Targeted NMR - urine

RAW_FILE_NAME = "unified-nmr-targeted-urine.xlsx"
RAW_FILE_NAME_V1 = "NMR_Urine_metabolites_CIC (Spain-Greece).xlsx"


df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME))
print(df)
print(df.columns)

df = clean_site_column(df)
df = clean_patient_column(df)

print(df.columns)
string_cols = ["patient", "visit", "site"]
float_cols = [s for s in df.columns if s not in string_cols]
df = change_types(df, string_cols=string_cols, float_cols=float_cols)

df = df[string_cols + [col for col in df.columns if col not in string_cols]]

# variable names
names = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME_V1), sheet_name="References")
print(names)
names["metabolite"] = names["metabolite"].str.lower().str.replace(" ", "-").str.replace("_", "-")

column_units = {}
column_info = {}
for metabolite, unit, vmin, vmax in names.itertuples(index=False, name=None):
    #assert metabolite in df.columns, f"Variable {metabolite} not among columns."
    if metabolite in df.columns:
        column_units[metabolite] = unit
        if not empty_filed(vmin):
            column_info[metabolite] = {"vmin": vmin}
        column_info[metabolite] = {"vmax": vmax}

print(df)
print(column_info)
test_data_frame(df)


test_data_frame(df)

metadata = DataFrameMetadata(df, "2.0", comment="Targeted NMR - urine, unified", categorical_features=["visit", "site"],
                             column_units=column_units, column_info=column_info)

save(metadata, "nmr-targeted-urine")

print(df.columns)
print(df)
