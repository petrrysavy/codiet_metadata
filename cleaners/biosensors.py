from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save

### Lipidomics - DBS and red blood celss

RAW_FILE_NAME = "BiosensorsMicrocaya_data_combined_jan2025.xlsx"

df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME))
print(df)
print(df.columns)

df = df.dropna(how="all")  # Remove completely empty rows

df = df.drop(columns=["volunteer_id"])
df[['patient', 'visit']] = df['sample_id'].str.extract(r'cd_(\d+)_V(\d)')
df['patient'] = 'CD-' + df['patient']
df['visit'] = 'V' + df['visit']
print(df["subcutaneous_fat"].unique())
all_zeros = ["subcutaneous_fat", "visceral_fat", "abdominal_fat",
                      "v/s_ratio(visceral_fat_area/subcutaneous_fat_area_ratio)", "sfa(subcutaneous_fat_area)",
                      "khz_50_ab_impedance", "khz_250_ab_impedance", "angle-r", "angle_l"]
for col in all_zeros:
    assert (df[col].dropna() == 0.0).all(), f"Column {col}"
df = df.drop(columns=all_zeros)
df = df.drop(columns=["sample_id"])

df = df.rename(columns={"recruitment_site": "site"})

df = column_names_remove_underscores(df)
df = column_names_to_lowercase(df)


# variable names
names = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME), sheet_name=1)
print(names)

names = names[names["variable"] != "sample_id"]
names["variable"] = names["variable"].replace("volunteer_id", "patient")
names["variable"] = names["variable"].replace("recruitment_site", "site")
names = names[~names["variable"].isin(all_zeros)]
column_comments, column_units, column_info = variable_comment_unit_df_other_to_dict(df, names, "sensor",
                                                                                    lambda s: s.lower().replace(" ", "-").replace("_", "-"))

df = replace_empty_with_na(df)

def convert_to_float(val):
    if isinstance(val, str):
        try:
            # Try direct float conversion first
            return float(val)
        except ValueError:
            # If it fails, fix formatting
            parts = val.split('.')
            if len(parts) > 2:
                whole = ''.join(parts[:-1])
                decimal = parts[-1]
                cleaned = whole + '.' + decimal
                try:
                    return float(cleaned)
                except ValueError:
                    return None
            else:
                return None
    elif isinstance(val, (int, float)):
        return float(val)
    else:
        return None


df['tp'] = df['tp'].apply(convert_to_float)
df['lf'] = df['lf'].apply(convert_to_float)
df['vlf'] = df['vlf'].apply(convert_to_float)
df['hf'] = df['hf'].apply(convert_to_float)
tolerance = 1e-2
mask = df[['tp', 'vlf', 'lf', 'hf']].notna().all(axis=1)
expected_tp = df.loc[mask, 'vlf'] + df.loc[mask, 'lf'] + df.loc[mask, 'hf']
assert np.allclose(df.loc[mask, 'tp'], expected_tp, atol=tolerance), "tp != vlf + lf + hf for some valid rows"


print(df.columns)
for c in df.columns:
    print(c)
string_cols = ["patient", "visit", "gender", "risk-group", "site", "wave-type", "ai-status", "ae-status", "pe-status",
               "hr-status", "apgcomment", "measure-sensor", "ans-activity", "ans-activity-status", "ans-balance-status",
               "stress-resilience-status", "stress-index-status", "fatigue-index-status", "mean-hrt-status",
               "electro-cardiac-stability-status", "ddrcomment", "vfl-(visceral-fat-level)"] # df['tp'] = df['tp'].apply(convert_to_float)
#TODO tp and vlf, lf, hf columns are strange, treating as strings - fixed 05/26/2025
date_cols = ["date-of-birth", "exam-date"]
categorical_features = ["gender", "risk-group", "site", "wave-type", "ai-status", "ae-status", "pe-status", "hr-status",
                        "ans-activity", "ans-activity-status", "ans-balance-status", "stress-resilience-status",
                        "stress-index-status", "fatigue-index-status", "mean-hrt-status",
                        "electro-cardiac-stability-status", "vfl-(visceral-fat-level)"]
int_cols = ["hr", "stress-resilience", "stress-index", "mean-hrt", "ectopic-beat", "height", "age", "inbody-score",
            "bmr-(basal-metabolic-rate)", "obesity-degree", "lower-limit-(obesity-degree-normal-range)",
            "upper-limit-(obesity-degree-normal-range)", "inbody-type", "local-id", "recommended-calorie-intake",
            "lower-limit-(bmr-normal-range)", "upper-limit-(bmr-normal-range)"]
float_cols = [s for s in df.columns if s not in string_cols and s not in date_cols and s not in int_cols]
df = change_types(df, string_cols=string_cols, float_cols=float_cols, date_cols=date_cols, int_cols=int_cols, safe=False)

df = df[["patient", "visit"] + [col for col in df.columns if col not in ["patient", "visit"]]]

test_data_frame(df)

metadata = DataFrameMetadata(df, "1.3", comment="Biosensors microcaya", categorical_features=["visit"],
                             column_comments=column_comments, column_units=column_units, column_info=column_info)

save(metadata, "biosensors")

print(df.columns)
print(df.dtypes)
print(df)
