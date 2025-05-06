import pandas as pd
import numpy as np


def empty_filed(value):
    return pd.isna(value) or pd.isnull(value) or value == "" or value == np.nan


def empty_field_series(series):
    return series.isna() | (series == "")
