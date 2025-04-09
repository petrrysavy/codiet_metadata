from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save
import re

RAW_FILE_NAME = "CODIET_LIPIDOMICS_TOTAL_AUTH.a.xlsx"

df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME), header=None)
df.iloc[3, 1] = "todrop"
df.iloc[3, 2] = "type"
df.columns = df.iloc[3]

df = column_names_remove_underscores(df)
df = column_names_remove_spaces(df)
df = column_names_to_lowercase(df)

print(df)
print(df.columns)

df = df.drop(df.index[342:345])
df = df.drop(df.index[7:10])
df = df.drop(df.index[2])


# Function to extract patient and visit
def extract_patient_visit(value):
    match = re.match(r'(CD\d+)_([Vv]\d+)_', value)
    if match:
        return match.group(1).replace("CD", "CD-"), match.group(2).upper()
    else:
        return pd.NA, pd.NA
# Apply to dataframe
df[['patient', 'visit']] = df["name"].apply(lambda x: pd.Series(extract_patient_visit(x)))
df = df.drop(columns=["name", "todrop"])
df = df.replace("qc", "control")


print(df.columns)
string_cols = ["patient", "visit", "type"]
float_cols = [s for s in df.columns if s not in string_cols]
print(df)

metadata = DataFrameMetadata(df, "1.3", comment="Lipidomics data, measured at AUTH. rows where patient and"
                                                "visit are pd.NA contain quality control data. Those rows are used"
                                                "to filter columns based on required quality. The quality column should"
                                                "ideally contain all the same value, therefore, all having more than"
                                                "(for example) 20% variance are dropped. Column names contain mass (m/z)."
                                                "The retention time in metadata is in minutes, m/z is the mass, CCS in Å²,"
                                                "and delta-ccs in %.",
                             categorical_features=["visit", "type"],
                             #  if isinstance(df.loc[0, col], float) else str(df.loc[0, col].iloc[0])
                             column_info={col: {"rentention-time": str(df.loc[0, col]),
                                                "m/z": str(df.loc[1, col]),
                                                "original-name": str(df.loc[3, col]),
                                                "molecular-formula": str(df.loc[4, col]),
                                                "ccs": str(df.loc[5, col]),
                                                "delta-ccs": str(df.loc[6, col])}
                                          for col in float_cols})
df = df.drop(df.index[0:6])
df = change_types(df, string_cols=string_cols, float_cols=float_cols)
df = df[string_cols + [col for col in df.columns if col not in string_cols]]
metadata.df = df

print(df)
test_data_frame(df, numeric_column_names=True)


save(metadata, "lipidomics")

print(df.columns)
print(df.dtypes)
print(df)
