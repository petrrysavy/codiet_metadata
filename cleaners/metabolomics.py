from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save
import re

RAW_FILE_NAME = "CODIET_METABOLOMICS_AUTH.a.xlsx"

df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME), header=None)
df.columns = df.iloc[1]
print(df)
print(df.columns)

print(df.loc[0, 438.3787].iloc[0])


df = df.drop(df.index[2:8])


# Function to extract patient and visit
def extract_patient_visit(value):
    match = re.match(r'(CD\d+)_([Vv]\d+)_', value)
    if match:
        return match.group(1).replace("CD", "CD-"), match.group(2).upper(), 'sample'
    else:
        return pd.NA, pd.NA, 'control'
# Apply to dataframe
df[['patient', 'visit', 'type']] = df['m/z'].apply(lambda x: pd.Series(extract_patient_visit(x)))
df = df.drop(columns="m/z")

print(df.columns)
string_cols = ["patient", "visit", "type"]
float_cols = [s for s in df.columns if s not in string_cols]
df = change_types(df, string_cols=string_cols, float_cols=float_cols)
df = df[string_cols + [col for col in df.columns if col not in string_cols]]

print(df.loc[0, 438.3787])

metadata = DataFrameMetadata(df, "1.3", comment="Metabolomics data, measured at AUTH. rows where patient and"
                                                "visit are pd.NA contain quality control data. Those rows are used"
                                                "to filter columns based on required quality. The quality column should"
                                                "ideally contain all the same value, therefore, all having more than"
                                                "(for example) 20% variance are dropped. Column names contain mass (m/z).",
                             categorical_features=["visit", "type"],
                             # some strange error in some columns ... there are pd.series?
                             column_info={col: {"rentention-time": str(df.loc[0, col]) if isinstance(df.loc[0, col], float) else str(df.loc[0, col].iloc[0])} for col in float_cols})
df = df.drop(df.index[0])
df = df.drop(df.index[0])
metadata.df = df

print(df)
test_data_frame(df, numeric_column_names=True)


save(metadata, "metabolomics")

print(df.columns)
print(df.dtypes)
print(df)
