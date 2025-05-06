from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save
import re

### Blood biochemistry

# Do not change order'
SITES = ["Cork", "Greece", "ICL", "UVEG", "Bilbao"]  # Bilbao last to keep units and range from Bilbao

RAW_FILE_NAME = "nmr_serum_metabolomics_CoDiet_CICbioGUNE.v2.xlsx"

merged_df = pd.DataFrame()
columns_info = {}
for site in SITES:
    df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), "Blood biochemistry from "+site+"_V1_V3.xlsx"), index_col=0, header=None)
    names = df.iloc[:, [0, 1]]
    df = df.drop(df.columns[[0, 1]], axis=1)
    df = df.T
    df.columns = df.columns.str.replace(", blood", "")
    df.columns = df.columns.str.replace("count", "", regex=True)
    df.columns = df.columns.str.replace("Count", "", regex=True)
    df.columns = df.columns.str.replace("level", "", regex=True)
    df.columns = df.columns.str.replace(" ", "", regex=True)
    df = df.rename(columns={'Bloodparameter': 'sample-id'})
    #names = names.replace(", blood", "").replace("count", "", regex=True).replace("Count", "", regex=True).replace("level", "", regex=True).replace(" ", "", regex=True)

    # High/low markers, not needed actually
    df = df.replace(r"H\s", "", regex=True)
    df = df.replace(r"L\s", "", regex=True)
    df = df.replace(r"\*\sH\s", "", regex=True)
    df = df.replace(r"\*\sL\s", "", regex=True)
    df = df.replace(r"\*\s", "", regex=True)
    df = df.replace("No appropriate sample received: Please send a grey top sample.", pd.NA)
    df = df.replace("Regret, sample not received to Biochemistry lab at Charing cross site. Please repeat.", pd.NA)

    df = column_names_remove_spaces(df)
    df = column_names_remove_underscores(df)
    df = column_names_to_lowercase(df)
    #names = names.replace(" ", "-", regex=True).replace("--", "-", regex=True).replace("-/-", "/", regex=True).replace("_", "-", regex=True).lower()
    df = replace_empty_with_na(df)
    df.columns = df.columns.str.replace("cells", "cell")

    print(df.columns[df.columns.duplicated()])
    print(zip(df.columns, df.columns.duplicated()))
    if site not in ["Greece", "Bilbao"]:
        df.columns = [f"{col}count" if dup else col for col, dup in zip(df.columns, df.columns.duplicated())]

    df = df.rename(columns={"crp-c-reactiveprotein": "crp",
                    "aspartatetransferase": "aspartatotransaminase",
                    "aspartatotransaminase(ast)": "aspartatotransaminase",
                    "alanineaminotransferase(alt)": "alanineaminotransferase",
                    "alkalinephosphatasea": "alkalinephosphatase",
                    "alkalinephosphatase(alp)": "alkalinephosphatase",
                    "platelets": "platelet",
                    "mcv": "meancellvolume",
                    "meancellhaemconc": "meancellhaemoglobinconc",
                    "hgb": "haemoglobin",
                    "hctratio": "haematocrit",
                    "triglycerides": "triglyceride",
                    "25-ohvitamind": "vitamind",
                    "gamma-glutamyltransferase": "gammagtp"})

    df['site'] = site

    if site in ["Greece", "Bilbao"]:
        for dupl in ["lymphocyte", "monocyte", "eosinophil", "basophil"]:
            cols = list(df.columns)
            seen = False
            for i, col in enumerate(cols):
                if col == dupl:
                    if not seen:
                        cols[i] = f"{dupl}pct"
                        seen = True

            # Assign new column names
            df.columns = cols

    UVEGdict = {'neutrophil': 'neutrophilpct', "lymphocyte": "lymphocytepct", "monocyte": "monocytepct", "eosinophil": "eosinophilpct", "basophil": "basophilpct"}
    for i, col in enumerate(df.columns):
        if col in ["site", "sample-id"]: continue

        if site == "UVEG" and col in UVEGdict: col = UVEGdict[col]

        columns_info[col] = {"unit": names.iloc[i, 0], "range": names.iloc[i, 1]}

    def linear_transform(x, conversion_parameter):
        # Case 1: float — divide directly
        try:
            return float(x) / conversion_parameter
        except (ValueError, TypeError):
            pass

        # Case 2: string like "> 6", "<= 4.5", etc.
        if isinstance(x, str):
            pattern = r'([<>]=?\s*)(\d+(\.\d+)?)'
            if re.match(pattern, x.strip()):
                return re.sub(
                    pattern,
                    lambda m: f"{m.group(1)}{float(m.group(2)) / conversion_parameter}",
                    x
                )
        # Otherwise return unchanged
        return x

    if site in ["Cork", "ICL"]:  # different units!
        df['creatinine'] = df['creatinine'].apply(lambda x: linear_transform(x, 88.42))
        df['glucose'] = df['glucose'].apply(lambda x: linear_transform(x, 1.0/18))
        df['urea'] = df['urea'].apply(lambda x: linear_transform(x, 1.0/6.006))
        df['ldlcholesterol'] = df['ldlcholesterol'].apply(lambda x: linear_transform(x, 1.0/38.67))
        df['hdlcholesterol'] = df['hdlcholesterol'].apply(lambda x: linear_transform(x, 1.0/38.67))
        df['albumin'] = df['albumin'].apply(lambda x: linear_transform(x, 10))
        df['totalbilirubin'] = df['totalbilirubin'].apply(lambda x: linear_transform(x, 17.1))
        df['haemoglobin'] = df['haemoglobin'].apply(lambda x: linear_transform(x, 10))
        df['vitamind'] = df['vitamind'].apply(lambda x: linear_transform(x, 2.496))
        df['meancellhaemoglobinconc'] = df['meancellhaemoglobinconc'].apply(lambda x: linear_transform(x, 10))
        df['triglyceride'] = df['triglyceride'].apply(lambda x: linear_transform(x, 0.0113))


    if site in ["Cork", "ICL",  "UVEG"]:  # different units!
        df['crp'] = df['crp'].apply(lambda x: linear_transform(x, 17.1))

    if site in ["ICL"]:  # different units!
        df['haematocrit'] = df['haematocrit'].apply(lambda x: linear_transform(x, 0.01))
        df['cholesterol'] = df['cholesterol'].apply(lambda x: linear_transform(x, 1.0 / 38.67))
        df['vldl'] = df['vldl'].apply(lambda x: linear_transform(x, 0.259))

    # ORDER DEPENDENT
    if site in ["Greece"]:
        df['meanplateletvolume'] = df['meanplateletvolume'].apply(lambda x: linear_transform(x, 10))
        # GREECE has approximately three times higher mean paletet coount, might be an error

    if site in ["Greece", "Bilbao"]:
        # the only one with percentage
        df["neutrophilpct"] = df["neutrophil"]
        df["neutrophil"] = df["neutrophilblood"]
        df = df.drop(columns=['neutrophilblood'])

    if site in ["Greece", "UVEG"]:
        df['platelet'] = df['platelet'] * df['meanplateletvolume'] * 100
        df['hba1cifccstandardised'] = (df['hba1cifccstandardised'] - 2.15) * 10.929

    if site in ["UVEG"]:
        df = df.rename(columns=UVEGdict)

    merged_df = pd.concat([merged_df, df], ignore_index=True)
    print(merged_df)

df = merged_df
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

df[['patient', 'visit']] = df['sample-id'].str.extract(r'CD\s*-?\s*(\d+)\s*-?\s*V(\d)')
df['patient'] = 'CD-' + df['patient']
df['visit'] = 'V' + df['visit']
df = df.drop(columns=['sample-id'])

print(df.columns)
df = replace_empty_with_na(df)
string_cols = ["patient", "visit", "site", "glomerularfiltration(estimated)", "crp", "aspartatotransaminase",
               "crp", "crpmet", "gammagtp", "potassium", "totalbilirubin"]
float_cols = [s for s in df.columns if s not in string_cols]
df = change_types(df, string_cols=string_cols, float_cols=float_cols)

df = df[["patient", "visit", "site"] + [col for col in df.columns if col not in ["patient", "visit", "site"]]]

test_data_frame(df)

metadata = DataFrameMetadata(df, "1.3", comment="Targeted NMR - serum", categorical_features=["visit", "site"], column_info=columns_info)

save(metadata, "bloodbiochemistry")

print(df.columns)
print(df)
