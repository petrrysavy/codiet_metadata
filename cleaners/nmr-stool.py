from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save

type = "stool"

RAW_FILE_NAME = f"CD_WP2_NMR_{type}.csv"

df = pd.read_csv(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME), header=0)
print(df)
print(df.columns)

df['patient'] = 'CD-' + df['patient_ID'].astype(str)
df['visit'] = 'V' + df['visit'].astype(str)

df = df.rename(columns={"sampleWeight_g": "sample-weight"})
df = df.drop(columns=["patient_ID"])

df = column_names_to_lowercase(df)

string_cols = ["patient", "visit", "site", "gender"]
int_cols = ["age"]
float_cols = [s for s in df.columns if s not in string_cols and s not in int_cols and s]
df = change_types(df, string_cols=string_cols, float_cols=float_cols, int_cols=int_cols)

order_cols = ["patient", "visit", "site", "age", "gender", "sample-weight"]
df = df[order_cols + [col for col in df.columns if col not in order_cols]]

df["gender"] = df["gender"].replace("0", pd.NA)

print(df.columns)

test_data_frame(df, numeric_column_names=True)

metadata = DataFrameMetadata(df, "1.3", comment=f"NMR {type}", categorical_features=["visit", "gender"],
                             column_units={"sample-weight": "g"})

save(metadata, f"nmr-{type}")

print(df.columns)
print(df.dtypes)
print(df)
