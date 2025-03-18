import pandas as pd

def test_data_frame(df):
    assert "patient" in df.columns, "'patient' column is missing"
    assert "visit" in df.columns, "'visit' column is missing"
    assert df["patient"].str.fullmatch(r"CD-\d+").all(), "Some 'patient' values do not match the required format"
    assert df["visit"].str.fullmatch(r"V\d").all(), "Some 'visit' values do not match the required format"
    assert all(col.islower() for col in df.columns), "Not all column names are lowercase"
    if "gender" in df.columns:
        assert df["gender"].isin(["Male", "Female", pd.NA]).all(), "Column 'gender' contains invalid values"
    assert all(" " not in col for col in df.columns), "Column names contain spaces!"
