from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import clean_patient_column, column_names_to_lowercase, replace_empty_with_na, change_types
from metadata import DataFrameMetadata
from inputoutput import save

RAW_FILE_NAME = "CODIET_ALL COUNTRIES_SCFAS_STOOL.xlsx"

df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME), index_col=0)
print(df)

# expno.1 is duplicate
df = df.drop(columns=["SAMPLE_ID", "Comments", "expno.1"])
df = df.rename(columns={"PATIENT_ID": "patient", "VISIT(1,3)": "visit", "Aliquot Number": "aliquot-no",
                        "VOLUME(ML) PER ALIQOTE": "volume-per-aliqote", "SAMPLE TYPE": "type",
                        "PATIENT_AGE": "age", "PATIENT_GENDER": "gender",
                        "BOX_POSITION (Box number_ Row number_ Column number)": "box-position",
                        "Weight [g]": "sample-weight", "UHPLC H20 [mL]": "uhplc-h2o", "NMR rack": "nmr-rack"})
df["visit"] = df["visit"].str.extract(r"^(V\d+)")
# ask about the visit number - right use the first value (V1/V3)

print(df.columns)

df["volume-per-aliqote"] = df["volume-per-aliqote"].replace("1 Pot", 1)

df = clean_patient_column(df)
df = column_names_to_lowercase(df)
df = replace_empty_with_na(df)

df = change_types(df, string_cols=["patient", "visit", "type", "site", "gender", "box-position", "position"],
                  int_cols=["aliquot-no", "volume-per-aliqote", "age", "nmr-rack", "expno"],
                  float_cols=["sample-weight", "uhplc-h2o", "acetate", "butyrate", "formate", "propionate"],
                  date_cols=["day"])

test_data_frame(df)

comments = {
    "volume-per-aliqote": "The number of pots given by the participant.",
    "sample-weight": "Weight of the sample in grams.",
    "box-position": "BOX_POSITION (Box number_ Row number_ Column number)",
    "uhplc-h2o": "UHPLC H20 [mL]"
}
metadata = DataFrameMetadata(df, "1.1", column_comments=comments, comment="SCAFS, stool data",
                             categorical_features=["visit", "type", "gender"])

save(metadata, "scafs-stool")

print(df.columns)
print(df)
