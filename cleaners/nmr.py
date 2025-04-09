from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save

TYPES = ["serum", "urine"]

for type in TYPES:
    RAW_FILE_NAME = f"CD_WP2_NMR_{type}.csv"

    df = pd.read_csv(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME), header=0)
    print(df)
    print(df.columns)

    df['patient'] = 'CD-' + df['patientID'].astype(str)
    df['visit'] = 'V' + df['visit'].astype(str)

    df = df.rename(columns={"partnerSite": "site", "machineName": "machine-name"})
    df["exam-date"] = pd.to_datetime(df["acquisitionDate"] + " " + df["acquisitionTime"])

    df = df.drop(columns=["acquisitionDate", "acquisitionTime", "patientID"])

    df = column_names_to_lowercase(df)

    string_cols = ["patient", "visit", "site", "machine-name", "aunmp", "exp"]
    #TODO tp and vlf, lf, hf columns are strange, treating as strings
    date_cols = ["exam-date"]
    float_cols = [s for s in df.columns if s not in string_cols and s not in date_cols and s]
    df = change_types(df, string_cols=string_cols, float_cols=float_cols, date_cols=date_cols)

    df = df[string_cols + [col for col in df.columns if col not in string_cols]]

    print(df.columns)

    test_data_frame(df, numeric_column_names=True)

    metadata = DataFrameMetadata(df, "1.3", comment=f"NMR {type}", categorical_features=["visit"])

    save(metadata, f"nmr-{type}")

    print(df.columns)
    print(df.dtypes)
    print(df)
