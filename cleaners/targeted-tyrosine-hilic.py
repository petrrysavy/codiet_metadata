from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save
import re

RAW_FILE_NAME = "CODIET MATRIX targeted methods AUTH SERUM URINE.c.xlsx"

print(RAW_FILE_NAME)

# Other sheet in saccharides and acyl carnities!!!
df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME), header=2, sheet_name="URINE")
print(df)
print(df.columns)

df[['patient', 'visit']] = df['Participants ID / Compounds '].str.extract(r'CD_(\d+)_V(\d)')
df['patient'] = 'CD-' + df['patient']
df['visit'] = 'V' + df['visit']

df = df.drop(columns="Participants ID / Compounds ")

df = column_names_to_lowercase(df)
df = column_names_remove_spaces(df)
df = replace_empty_with_na(df) # works for <LOQ as well
df = column_names_remove_underscores(df)

tyrosine = df.columns[0:33]
print(tyrosine)
hilic = df.columns[33:(33+51)]
print(hilic)

print(df.columns)
string_cols = ["patient", "visit"]
float_cols = [s for s in df.columns if s not in string_cols]
df = change_types(df, string_cols=string_cols, float_cols=float_cols)
df = df[string_cols + [col for col in df.columns if col not in string_cols]]

test_data_frame(df)

metadata = DataFrameMetadata(df, "1.3", comment="Targeted Tyrosine - Tryptophan Pathway and HILLIC acids, urine, measured at AUTH.",
                             categorical_features=["visit"],
                             column_info={col: {"method": ("tyrosine" if col in tyrosine else "hilic")} for col in float_cols})

save(metadata, "targeted-tyrosine-hilic")

print(df.columns)
print(df.dtypes)
print(df)
