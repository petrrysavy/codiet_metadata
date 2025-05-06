from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save

### MASS SPECTROMETRY - serum

RAW_FILE_NAME = "nmr_serum_metabolomics_CoDiet_CICbioGUNE.v2.xlsx"

df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME))
print(df)
print(df.columns)

df = column_names_remove_spaces(df)
df = column_names_remove_underscores(df)
df = column_names_to_lowercase(df)
df.columns = df.columns.str.replace("--", "-", regex=True)

df[['patient', 'visit']] = df['sample-id'].str.extract(r'CD-(\d+)-V(\d)')
df['patient'] = 'CD-' + df['patient']
df['visit'] = 'V' + df['visit']
df = df.drop(columns=['sample-id'])

print(df.columns)
string_cols = ["patient", "visit"]
float_cols = [s for s in df.columns if s not in string_cols]
df = change_types(df, string_cols=string_cols, float_cols=float_cols)

df = df[string_cols + [col for col in df.columns if col not in string_cols]]

test_data_frame(df)

metadata = DataFrameMetadata(df, "1.3", comment="Targeted NMR - serum", categorical_features=["visit"])

save(metadata, "nmr-targeted-serum")

print(df.columns)
print(df)
