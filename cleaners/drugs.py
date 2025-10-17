from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save
import re

RAW_FILE_NAME = "drugs and supplements CoDiet WP2 all sites.xlsx"

df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME))
print(df)
print(df.columns)

df = df.rename(columns={"Participant  ": "patient", "Site Collection": "site", "Sex": "gender", "Drugs": "xdr"})
df['visit'] = 'V1'

df = column_names_to_lowercase(df)
df = column_names_remove_spaces(df)
df = replace_empty_with_na(df) # works for <LOQ as well
df = clean_patient_column(df)
df = clean_site_column(df)
df = clean_gender_column(df)

cols_to_join = df.columns[5:9]
df['drugs'] = (
    df[cols_to_join]
    .astype(str)
    .replace(['nan', 'None', '', "<NA>"], pd.NA)
    .apply(lambda x: '; '.join(x.dropna()), axis=1)
)
df = df.drop(df.columns[5:9], axis=1)

print(df.columns)
string_cols = ["patient", "visit", "gender", "site", "food-supplements", "drugs"]
df = change_types(df, string_cols=string_cols)
df = df[["patient", "visit"] + [col for col in df.columns if col not in ["patient", "visit"]]]

test_data_frame(df)

metadata = DataFrameMetadata(df, "1.3", comment="Dugs and supplements",
                             categorical_features=["visit", "gender", "site"])

save(metadata, "drugs")

print(df.columns)
print(df.dtypes)
print(df)
