from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save
import re

RAW_FILE_NAME = "Blood pressure values all sites WP2.xlsx"

df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME))
print(df)
print(df.columns)

df = df.rename(columns={"Participant  ": "patient", "Site Collection": "site", "Systolic Blood Pressure (mm Hg)": "systolic",
                        "Diastolic Blood Pressure (mm Hg)": "diastolic", "hypertension/medication": "hypertension-medication-note",
                        "Sex": "gender"})
df['visit'] = 'V1'

df = column_names_to_lowercase(df)
df = column_names_remove_spaces(df)
df = replace_empty_with_na(df) # works for <LOQ as well
df = clean_patient_column(df)
df = clean_site_column(df)
df = clean_gender_column(df)

print(df.columns)
string_cols = ["patient", "visit", "hypertension-medication-note"]
int_cols = ["age"]
float_cols = ["systolic", "diastolic"]
df = change_types(df, string_cols=string_cols, int_cols=int_cols, float_cols=float_cols)
df = df[["patient", "visit"] + [col for col in df.columns if col not in ["patient", "visit"]]]

test_data_frame(df)

metadata = DataFrameMetadata(df, "1.3", comment="Blood pressure.",
                             categorical_features=["visit", "gender", "site"],
                             column_units={col: "mm Hg" for col in ["systolic", "diastolic"]})

save(metadata, "bloodpressure")

print(df.columns)
print(df.dtypes)
print(df)
