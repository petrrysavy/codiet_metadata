from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save
import re

### Metaphlan metabolomics

for type in ["filtered", "unfiltered"]:
    # Do not change order'
    RAW_FILE_NAME = f"metaphlan_species_profile_{type}_v1.csv"

    df = pd.read_csv(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME), index_col=0, header=None)

    #df = df.drop(df.columns[[0, 1]], axis=1)
    df = df.T
    fullnames = df.columns[1:]

    def rename_column(col, allcolnames):
        if col == "UNCLASSIFIED":
            return col.lower()
        if empty_filed(col):
            return ""

        parts = col.split("|")
        species_parts = [p for p in parts if p.startswith("s__")]
        if species_parts:
            species = species_parts[-1][3:]  # remove 's__'
            count = allcolnames.str.contains(species_parts[-1]).sum()
            if count > 1:
                strain_parts = [p for p in parts if p.startswith("t__")]
                strain = strain_parts[-1][3:]
                return f"{species.lower().replace("_", "-")}-{strain.lower()}"
            return species.lower().replace("_", "-")
        else:
            return col  # fallback if no 's__' found


    # Apply the renaming
    df.columns = [rename_column(col, fullnames) for col in df.columns]

    first_col = df.columns[0]

    # Define the regex pattern
    pattern = r"^.+visit\d+_metaphlan$"
    # Filter rows that match the pattern
    df = df[df[first_col].str.match(pattern, na=False)]

    # Extract patient and visit
    df["patient"] = df[first_col].str.extract(r"^CD_(\d+)visit")[0]
    df['patient'] = 'CD-' + df['patient']
    df["visit"] = "V" + df[first_col].str.extract(r"visit(\d+)")[0]

    # Drop the original first column
    df = df.drop(columns=[first_col])

    print(df.columns)
    df = replace_empty_with_na(df)
    string_cols = ["patient", "visit"]
    float_cols = [s for s in df.columns if s not in string_cols]
    df = change_types(df, string_cols=string_cols, float_cols=float_cols)

    df = df[string_cols + [col for col in df.columns if col not in string_cols]]

    test_data_frame(df)

    column_comments = {rename_column(col, fullnames): col for col in fullnames}
    metadata = DataFrameMetadata(df, "1.3", comment="Metaphlan metabolomics data", categorical_features=["visit", "site"], column_comments=column_comments)

    print(df.columns)
    print(df)
    save(metadata, f"metaphlan-{type}")

