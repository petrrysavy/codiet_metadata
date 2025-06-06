import numpy as np
import pandas as pd
from utils import empty_filed
from datetime import datetime, time



def clean_patient_column(df):
    df["patient"] = df["patient"].str.replace(r"CD_(\d+)", r"CD-\1", regex=True)
    return df


def replace_empty_with_na(df):
    """Replaces all empty strings, None, and NaN values with pd.NA in a DataFrame."""
    return df.replace(["", None, np.nan, "<LOQ", "N/A", " "], pd.NA)


def column_names_to_lowercase(df):
    df.columns = df.columns.str.lower()
    return df


def column_names_remove_spaces(df):
    df.columns = df.columns.str.replace(" ", "-", regex=True)
    df.columns = df.columns.str.replace("--", "-", regex=True)
    df.columns = df.columns.str.replace("-/-", "/", regex=True)
    df.columns = df.columns.str.replace(".", "-", regex=False)
    return df


def column_names_remove_underscores(df):
    df.columns = df.columns.str.replace("_", "-", regex=True)
    return df


def variable_comment_unit_df_to_dict(df, names, name_lambda):
    column_comments = {}
    column_units = {}
    for variable, comment, unit in names.itertuples(index=False, name=None):
        variable = name_lambda(variable)
        assert variable in df.columns

        if not empty_filed(comment):
            column_comments[variable] = comment
        if not empty_filed(variable):
            column_units[variable] = unit

    return column_comments, column_units


def variable_comment_unit_df_other_to_dict(df, names, other_info_name, name_lambda):
    column_comments = {}
    column_units = {}
    column_info = {}
    for variable, comment, unit, other in names.itertuples(index=False, name=None):
        variable = name_lambda(variable)
        assert variable in df.columns, f"Variable {variable} not among columns."

        if not empty_filed(comment):
            column_comments[variable] = comment
        if not empty_filed(unit):
            column_units[variable] = unit
        if not empty_filed(other):
            column_info[variable] = {other_info_name: other}

    return column_comments, column_units, column_info


def change_types(df, int_cols=[], float_cols=[], string_cols=[], date_cols=[], bool_cols=[], datetimetime_cols=[], safe=True):
    d = {}
    for col in int_cols:
        d[col] = "Int64"
    for col in float_cols:
        d[col] = "Float64"
    for col in string_cols:
        d[col] = "string"
    for col in bool_cols:
        d[col] = "boolean"
    for col in datetimetime_cols:
        d[col] = "string"

    if safe:
        df = df.astype(d)
    else:
        df = df.astype(d, errors="ignore")

    for col in date_cols:
        df[col] = pd.to_datetime(df[col], format='mixed')

    def parse_time(x):
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(x, fmt).time()
            except ValueError:
                continue
        raise ValueError(f"Time format not recognized: {x}")
    for col in datetimetime_cols:
        #print(df[df[col].apply(lambda x: isinstance(x, float))])
        df[col] = df[col].apply(lambda x: x if empty_filed(x) or isinstance(x, time) else parse_time(x))
    return df
