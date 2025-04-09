import pandas as pd

def test_data_frame(df, numeric_column_names = False):
    assert "patient" in df.columns, "'patient' column is missing"
    assert df.columns[0] == "patient", "patient column must be first"
    assert "visit" in df.columns, "'visit' column is missing"
    assert df.columns[1] == "visit", "visit column must be second"
    assert df["patient"].str.fullmatch(r"CD-\d+").all(), "Some 'patient' values do not match the required format"
    assert df["visit"].str.fullmatch(r"V\d").all(), f"Some 'visit' values do not match the required format {df["visit"].unique()}"
    #TODO clean this one
    assert all(((numeric_column_names and isinstance(col, float)) or col.islower()) or (numeric_column_names and col.replace(".", "").isdigit()) for col in df.columns),\
        "Not all column names are lowercase"
    if "gender" in df.columns:
        assert df["gender"].isin(["Male", "Female", pd.NA]).all(), "Column 'gender' contains invalid values"
    assert all(isinstance(col, float) or " " not in col for col in df.columns), "Column names contain spaces!"
