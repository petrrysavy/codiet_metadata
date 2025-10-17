from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save
import re

RAW_FILE_NAME = "biochemical data all converted values.xlsx"

df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME))
print(df)
print(df.columns)

df[['patient', 'visit']] = df['ΙD participant / Compound '].str.extract(r'CD[_\-\s]*(\d+)[_\-\s]*V(\d)')
df['patient'] = 'CD-' + df['patient']
df['visit'] = 'V' + df['visit']
df = df.drop(columns=["ΙD participant / Compound ", "Timepoint"])
df = df.rename(columns={"Site Collection": "site", "NEU (%)": "neu-pct (%)", "LYM (%)": "lym-pct (%)", "MONO (%)": "mono-pct (%)",
                        "BASO (%)": "baso-pct (%)", "EOS (%)": "eos-pct (%)"})

# Extract base names and units
unit_dict = {}
new_columns = ["patient", "visit", "site"]
df = df[new_columns + [col for col in df.columns if col not in new_columns]]

for col in df.columns:
    if col not in new_columns:
        match = re.match(r"^(.*?)\s*\((.*?)\)$", col)
        if match:
            name, unit = match.groups()
            new_columns.append(name.strip())
            unit_dict[name.strip()] = unit.strip()
        else:
            assert False

# Rename columns
df.columns = new_columns

df = column_names_to_lowercase(df)
df = column_names_remove_spaces(df)
print(df["site"].unique())
df = clean_site_column(df)
unit_dict = {k.lower().replace(' ', '-'): v for k, v in unit_dict.items()}

print(df.columns)
string_cols = ["patient", "visit", "site", "tbil", "crp", "sgot"]
float_cols = [s for s in df.columns if s not in string_cols]
df = change_types(df, string_cols=string_cols, float_cols=float_cols)

test_data_frame(df)

metadata = DataFrameMetadata(df, "2.0", comment="Blood biochemistry", categorical_features=["visit", "site"],
                             column_units=unit_dict)

save(metadata, "bloodbiochemistry")

print(df.columns)
print(df.dtypes)
print(df)
