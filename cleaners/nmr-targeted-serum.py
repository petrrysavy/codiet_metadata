from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save
import re
from scipy import stats

### MASS SPECTROMETRY - serum

RAW_FILE_NAME = "nmr_serum_metabolomics_CoDiet_CICbioGUNE.v2.xlsx"
RAW_FILE_NAME_2 = "CODIET_UK_IRELAND_SERUM_QUANTITATIVE_METABOLITES_IGP_corrected(1).xlsx"

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
df['site'] = "Bilbao"
df = df.drop(columns=['sample-id'])

### THE second dataset
sheet1 = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME_2), sheet_name=0)
sheet2 = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME_2), sheet_name=1)
sheet3 = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME_2), sheet_name=2)
for sheet in [sheet1, sheet2, sheet3]:
    sheet.drop(sheet.columns[7:10], axis=1, inplace=True)
    sheet.rename(columns={"PATIENT_ID": "patient", "VISIT(1,3)": "visit", "VOLUME(ML) PER ALIQOTE" : "volume-per-aliqote",
                          "BOX_POSITION (Box number_ Position number)": "box-position", "SITE": "site"}, inplace=True)
    sheet.drop(columns=["SAMPLE TYPE", "SAMPLE_ID for each site"], inplace=True)
    if "RUN ORDER" in sheet.columns: sheet.drop(columns=["RUN ORDER"], inplace=True)#  run order is expno
    print(sheet)
    print(sheet.columns)

on_cols = ['patient', 'visit', 'volume-per-aliqote', "site", 'box-position']
df2 = sheet1.merge(sheet2, on=on_cols, how='outer').merge(sheet3, on=on_cols, how='outer')
df2 = column_names_to_lowercase(df2)
df2 = column_names_remove_underscores(df2)
print(df2)
print(df2.columns)

unit_dict = {"volume-per-aliqote": "mL"}
new_columns = []

for col in df2.columns:
    match = re.match(r"^(.*?)\s*\[(.*?)\]$", col)
    if match:
        name, unit = match.groups()
        new_columns.append(name.strip())
        unit_dict[name.strip()] = unit.strip()
    else:
        new_columns.append(col)

# Rename columns
df2.columns = new_columns
df2 = column_names_remove_spaces(df2)
unit_dict = {k.lower().replace(' ', '-'): v for k, v in unit_dict.items()}

df.rename(columns={"n,n-dimethylglycine": "n-dimethylglycine"}, inplace=True)
df2.rename(columns={"exp-no-": "exp-no", "glyc": "pacs-glyc", "glyc/spc": "pacs-glyc/spc",  "glyca": "pacs-glyca",
                    "glycb": "pacs-glycb", "spc": "pacs-spc"}, inplace=True)
df2.drop(columns=["nmr-expno"], inplace=True)  # duplicate

# some cleanup
df2 = df2.replace("V1 (Atlantia V2)", "V1")
df2 = df2.replace("V3 (Atlantia V4)", "V3")
df2 = df2.replace("0.5mL", "0.5")

### EOThe second dataset

print("=========================")
print(df2.columns)
print(df.columns)
print("intersection: ")
print(df.columns.intersection(df2.columns))
print("df difference df2")
print(df.columns.difference(df2.columns))
print("df2 difference df")
print(df2.columns.difference(df.columns))
print("=========================")

# TEST for column intersections!
print("========== t-test ==============")
for col in df.columns.intersection(df2.columns):
    if col not in ["patient", "visit", "site"]:
        _, pval = stats.ttest_ind(df[col], df2[col], nan_policy='omit')
        mean_diff = abs(df[col].mean() - df2[col].mean())
        pooled_std = np.sqrt((df[col].var() + df2[col].var()) / 2)
        cohens_d = mean_diff / pooled_std
        #if pval >= 0.05:
        #    print(f"Column {col} has pvalue of {pval}") # too many false-positives
        if cohens_d > 0.5:
            print(f"Column {col} has Cohen's d of {cohens_d}")

print(df.columns)

df = pd.concat([df, df2], ignore_index=True)
df = clean_patient_column(df)
df = clean_site_column(df)

string_cols = ["patient", "visit", "site", 'box-position']
int_cols = ["exp-no"]
float_cols = [s for s in df.columns if s not in string_cols and s not in int_cols]
df = change_types(df, string_cols=string_cols, float_cols=float_cols, int_cols=int_cols)

prepend_cols = ["patient", "visit", "site", 'box-position', "volume-per-aliqote", "exp-no"]
df = df[prepend_cols + [col for col in df.columns if col not in prepend_cols]]

test_data_frame(df)

metadata = DataFrameMetadata(df, "2.0", comment="Targeted NMR - serum", categorical_features=["patient", "visit", "site"], column_units=unit_dict)

save(metadata, "nmr-targeted-serum")

print(df.columns)
print(df)
