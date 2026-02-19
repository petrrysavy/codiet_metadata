from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save

### Lipidomics - DBS and red blood celss

RAW_FILE_NAME = "lipidomics_dbs_rbc_combined_AZTI.xlsx"
RAW_FILE_NAME_RBC = "lipidomics_rbc_updated 12nov2025.xlsx"
RAW_FILE_NAME_DBS = "lipidomic_dbs_updated 12nov2025.xlsx"

rbc = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME_RBC))
dbs = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME_DBS))
print(rbc)
print(dbs)
df = pd.merge(rbc, dbs, on="sample_id", how="outer")

print(df)
print(df.columns)

df = df.drop(columns=["visit", "volunteer_ID"])
df[['patient', 'visit']] = df['sample_id'].str.extract(r'CD\s*[-_]?\s*(\d+)[AB]?\s*[-_]?\s*V(\d)')
df['patient'] = 'CD-' + df['patient']
df['visit'] = 'V' + df['visit']
df = df.drop(columns=["sample_id"])
df = clean_patient_column(df)
df = column_names_remove_underscores(df)
df = column_names_to_lowercase(df)


# variable names
names = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME), sheet_name=1)
print(names)

column_comments, column_units = variable_comment_unit_df_to_dict(df, names, lambda s: s.lower().replace("_", "-"))

df = replace_empty_with_na(df)

print(df.columns)
string_cols = ["patient", "visit"]
float_cols = [s for s in df.columns if s not in string_cols]
df = change_types(df, string_cols=string_cols, float_cols=float_cols)

df = df[string_cols + [c for c in df.columns if c not in string_cols]]

test_data_frame(df)

metadata = DataFrameMetadata(df, "2.0", comment="Lipidomics - dry blood and red blood cells", categorical_features=["visit"],
                             column_comments=column_comments, column_units=column_units)

save(metadata, "lipidomics-dbs-rbc")

print(df.columns)
print(df.dtypes)
print(df)
