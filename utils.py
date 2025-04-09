import pandas as pd
import numpy as np


def empty_filed(value):
    return pd.isna(value) or pd.isnull(value) or value == "" or value == np.nan
