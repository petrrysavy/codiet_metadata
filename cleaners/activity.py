from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save

RAW_FILE_NAME = "Activity_Summarize Data_All.xlsx"

SITES = {"London": "ICL", "Greece": "Greece", "Cork": "Cork", "Bilbao": "Bilbao", "Valencia": "UVEG"}

merged_df = pd.DataFrame()

for site, site_renamed in SITES.items():
    df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME), sheet_name=site)
    df = replace_empty_with_na(df)
    df = df.dropna(how='all')  # drop empty rows

    # Remove trailing whitespace from all string entries
    df = df.applymap(lambda x: x.rstrip() if isinstance(x, str) else x)

    # Drop all mean rows
    df = df[~((df.iloc[:, 1] == 'Mean') | (df.iloc[:, 2] == 'Mean'))]

    # for Cork, remove empty lines specially (date format null > 00:00)
    if site == 'Cork':
        df = df[~(df.iloc[:, 1].apply(lambda x: empty_filed(x)) & df.iloc[:, 2].apply(lambda x: empty_filed(x)))]

    # fill empty index columns (NICE gpt trick :) )
    df.iloc[:, 0] = df.iloc[:, 0].fillna(method='ffill')
    df.iloc[:, 1] = df.iloc[:, 1].fillna(method='ffill')

    df.columns.values[0] = 'patient'
    df.columns.values[1] = 'visit'
    df = column_names_to_lowercase(df)
    df = column_names_remove_spaces(df)
    df = column_names_remove_underscores(df)

    df['site'] = site_renamed

    df['patient'] = df['patient'].str.replace(r'^CD(?=\d{3,})', 'CD-', regex=True)

    merged_df = pd.concat([merged_df, df], ignore_index=True)

df = merged_df

# EMPTY CD-053/V3 and others !!!
print(df.iloc[160:180,:])
mask = (pd.isna(df["day-number"]) & (pd.isna(df["steps"])) & pd.isna(df["non-wear"]) & pd.isna(df["sleep"])
        & pd.isna(df["sedentary"]) & pd.isna(df["light"]) & pd.isna(df["moderate"]) & pd.isna(df["vigorous"]))
print(mask[160:180])
df = df[~mask]


int_cols = ["day-number", "steps", "non-wear", "sleep", "sedentary", "light", "moderate", "vigorous"]
df = change_types(df, string_cols=["patient", "visit", "site"],
                  int_cols=int_cols, safe=False)

#for col in int_cols:
#    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    #df[col] = df[col].replace(0, pd.NA)
#df["sleep-efficiency"] = df["sleep-efficiency"].replace(0, pd.NA)



#safer this way:
mask = ((df["steps"] == 0) & (df["non-wear"] == 0) & (df["sleep"] == 0)
        & (df["sedentary"] == 0) & (df["light"] == 0) & (df["moderate"] == 0) & (df["vigorous"] == 0))
df.loc[mask, ["steps", "non-wear", "sleep", "sedentary", "light", "moderate", "vigorous"]] = pd.NA



df = df[['patient', 'visit', 'site'] + [col for col in df.columns if col not in ['patient', 'visit', 'site']]]

test_data_frame(df)

units = {col: "s" for col in ["non-wear", "sleep", "sedentary", "light", "moderate", "vigorous"]}
metadata = DataFrameMetadata(df, "1.3", column_units=units, comment="Activity wearable data",
                             categorical_features=["visit", "site"])

save(metadata, "activity")

print(df.columns)
print(df)
