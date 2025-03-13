import numpy as np
import pandas as pd


def clean_patient_column(df):
    df["patient"] = df["patient"].str.replace(r"CD_(\d+)", r"CD-\1", regex=True)
    return df


def replace_empty_with_na(df):
    """Replaces all empty strings, None, and NaN values with pd.NA in a DataFrame."""
    return df.replace(["", None, np.nan], pd.NA)


def column_names_to_lowercase(df):
    df.columns = df.columns.str.lower()
    return df


def change_types(df, int_cols=[], float_cols=[], string_cols=[], date_cols=[]):
    d = {}
    for col in int_cols:
        d[col] = "Int64"
    for col in float_cols:
        d[col] = "Float64"
    for col in string_cols:
        d[col] = "string"

    df = df.astype(d)

    for col in date_cols:
        df[col] = pd.to_datetime(df[col])
    return df
