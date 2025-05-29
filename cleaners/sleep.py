from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save

RAW_FILE_NAME = "Sleep_Summarize Data_All.xlsx"

SITES = {"London": "ICL", "Greece": "Greece", "Cork": "Cork", "Bilbao": "Bilbao", "Valencia": "UVEG"}

merged_df = pd.DataFrame()

for site, site_renamed in SITES.items():
    #     data = pd.read_csv(file_path, sep=";", header=None, skip_blank_lines=True, encoding='windows-1252')
    df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME), sheet_name=site)
    df = replace_empty_with_na(df)
    df = df.dropna(how='all')  # drop empty rows

    # Remove trailing whitespace from all string entries
    df = df.applymap(lambda x: x.rstrip() if isinstance(x, str) else x)

    # Drop all mean rows
    df = df[~((df.iloc[:, 1] == 'Mean') | (df.iloc[:, 2] == 'Mean'))]

    # for Cork, remove empty lines specially (date format null > 00:00)
    if site == 'Cork':
        df = df[~(df.iloc[:, 1].apply(lambda x : empty_filed(x)) & df.iloc[:, 2].apply(lambda x : empty_filed(x)))]

    # fill empty index columns (NICE gpt trick :) )
    df.iloc[:, 0] = df.iloc[:, 0].fillna(method='ffill')
    df.iloc[:, 1] = df.iloc[:, 1].fillna(method='ffill')


    df.columns.values[0] = 'patient'
    df.columns.values[1] = 'visit'
    df = column_names_to_lowercase(df)
    df = column_names_remove_spaces(df)

    df['site'] = site_renamed

    df['patient'] = df['patient'].str.replace(r'^CD(?=\d{3,})', 'CD-', regex=True)
    df = df.drop(columns=['sleep-time-(24h)', 'rise-time-(24h)'])

    # for Bilbao, remove few empty lines, not all same > safer manually ...
    if site == 'Bilbao':
        df = df.iloc[1:]
        df = df[~((df['patient'].str.contains("CD-021")) & (df['visit'].str.contains("V1")))]
        df = df[~((df['patient'].str.contains("CD-095")) & (df['visit'].str.contains("V3")))]


    merged_df = pd.concat([merged_df, df], ignore_index=True)

df = merged_df

# TODO CORRUPTED VALUES CD-042/V1 !!!
df = df[~((df['patient'].str.contains("CD-042")) & (df['visit'].str.contains("V1")))]

int_cols = ["total-elapsed-bed-time", "total-sleep-time", "total-wake-time", "num-active-periods", "median-activity-length"]
df = change_types(df, string_cols=["patient", "visit", "site"],
                  int_cols=int_cols,
                  float_cols=["sleep-efficiency"],
                  date_cols=["night-starting"],
                  datetimetime_cols=['sleep-onset-time', 'rise-time'],
                  safe=False)

for col in int_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    #df[col] = df[col].replace(0, pd.NA)
#df["sleep-efficiency"] = df["sleep-efficiency"].replace(0, pd.NA)

#safer this way:
mask = ((df["total-elapsed-bed-time"] == 0) & (df["total-sleep-time"] == 0) & (df["total-wake-time"] == 0)
        & (df["num-active-periods"] == 0)) & (df["median-activity-length"] == 0) & (df["sleep-efficiency"] == 0)
df.loc[mask, ["total-elapsed-bed-time", "total-sleep-time", "total-wake-time", "num-active-periods", "median-activity-length", "sleep-efficiency"]] = pd.NA



df = df[['patient', 'visit', 'site'] + [col for col in df.columns if col not in ['patient', 'visit', 'site']]]

test_data_frame(df)

units = {
    "total-elapsed-bed-time": "s",
    "total-sleep-time": "s",
    "total-wake-time": "s",
    "median-activity-length": "s",
    "sleep-efficiency": "%"
}
metadata = DataFrameMetadata(df, "1.3", column_units=units, comment="Sleep data",
                             categorical_features=["visit", "site"])

save(metadata, "sleep")

print(df.columns)
print(df)
