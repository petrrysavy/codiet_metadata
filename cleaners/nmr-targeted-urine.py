from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save

### Targeted NMR - urine

RAW_FILE_NAME = "NMR_Urine_metabolites_CIC (Spain-Greece).xlsx"

df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME), sheet_name="Absolute_values")
print(df)
print(df.columns)

df = column_names_remove_spaces(df)
df = column_names_remove_underscores(df)
df = column_names_to_lowercase(df)

df['site'] = df['experiment'].str.extract(r'ST_CoDiet_([^_]+)_Urine')
df['date'] = pd.to_datetime(df['experiment'].str.extract(r'NMR-(\d{8})')[0], format='%Y%m%d')

df[['patient', 'visit']] = df['nmr-id'].str.extract(r'CD-(\d+)-V(\d)[_-]Urine[_-]NMR.*')
df['patient'] = 'CD-' + df['patient']
df['visit'] = 'V' + df['visit']
df = df.drop(columns=['nmr-id', 'experiment'])

print(df.columns)
string_cols = ["patient", "visit", "site", "sample-type"]
date_cols = ["date"]
first_cols = string_cols+date_cols
float_cols = [s for s in df.columns if s not in first_cols]
df = change_types(df, string_cols=string_cols, float_cols=float_cols, date_cols=date_cols)

df = df[first_cols + [col for col in df.columns if col not in first_cols]]

# variable names
names = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME), sheet_name="References")
print(names)
names["metabolite"] = names["metabolite"].str.lower().str.replace(" ", "-").str.replace("_", "-")

column_units = {}
column_info = {}
for metabolite, unit, vmin, vmax in names.itertuples(index=False, name=None):
    assert metabolite in df.columns, f"Variable {metabolite} not among columns."

    column_units[metabolite] = unit
    if not empty_filed(vmin):
        column_info[metabolite] = {"vmin": vmin}
    column_info[metabolite] = {"vmax": vmax}

print(df)
print(column_info)
test_data_frame(df)

metadata = DataFrameMetadata(df, "1.3", comment="Targeted NMR - urine", categorical_features=["visit", "sample-type", "site"],
                             column_units=column_units, column_info=column_info)

save(metadata, "nmr-targeted-urine")

print(df.columns)
print(df)
