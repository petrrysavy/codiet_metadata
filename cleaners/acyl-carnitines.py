from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save
import re

RAW_FILE_NAME = "AcylCarnitines Serum Quatitiative AUTH.xlsx"

df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME))
print(df)
print(df.columns)

df[['patient', 'visit']] = df['ID PARTICIPANT / C COMPOUNDS (μM)'].str.extract(r'CD_(\d+)_V(\d)')
df['patient'] = 'CD-' + df['patient']
df['visit'] = 'V' + df['visit']

df = df.drop(columns="ID PARTICIPANT / C COMPOUNDS (μM)")

df = column_names_to_lowercase(df)
df = column_names_remove_spaces(df)
df = replace_empty_with_na(df) # works for <LOQ as well
df = column_names_remove_underscores(df)

print(df.columns)
string_cols = ["patient", "visit"]
float_cols = [s for s in df.columns if s not in string_cols]
df = change_types(df, string_cols=string_cols, float_cols=float_cols)
df = df[string_cols + [col for col in df.columns if col not in string_cols]]

test_data_frame(df)

metadata = DataFrameMetadata(df, "1.3", comment="Acyl carnitines, serum, measured at AUTH.",
                             categorical_features=["visit"],
                             column_units={col: "μΜ" for col in float_cols})

save(metadata, "acyl-carnitines")

print(df.columns)
print(df.dtypes)
print(df)
