from settings import *
from utils import empty_field_series
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save

RAW_FILE_NAME = "CoDiet Intake24 Data -All sites.xlsx"

df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME), index_col=None)
print(df)

df[['patient', 'visit']] = df['User ID'].str.extract(r'CD_(\d+)_V(\d)')
df['patient'] = 'CD-' + df['patient']
df['visit'] = 'V' + df['visit']

print(df[df['Description (en)'] != df['Description (local)']][['Description (en)', 'Description (local)']])

# assert (df['Description (en)'] == df['Description (local)']).all() - not true, but still duplicate
empty_cols = ['Food group (local)', 'As served weight factor', 'Missing food portion size']
for col in empty_cols:
    if not (empty_field_series(df[col])).all():
        print(df[col][~empty_field_series(df[col])])


df = df.drop(columns=["User ID", 'Description (local)', "Energy (kJ)"]) # No need to have two linearly dependent columns
df = df.drop(columns=empty_cols)
df = df.rename(columns={"Food group (en)": "Food group", "Serving size (g/ml)": "Serving size",
                        "Leftovers (g/ml)": "Leftovers", "Portion size (g/ml)": "Portion size",
                        "Energy (kcal)": "Energy", "Description (en)": "Description"})

df = column_names_to_lowercase(df)
df = column_names_remove_spaces(df)
df = replace_empty_with_na(df)

string_cols = ["patient", "visit", "cooking-oil-used", "diet", "food-amount", "reason-for-unusual-food-amount", "meal-name",
              "meal-time", "food-source", "search-term", "intake24-food-code", "description", "food-group", "brand",
              "missing-food-leftovers",  "missing-food-description", "sub-group-code"]
bool_cols = ["ready-meal", "reasonable-amount"]
url_cols = ["serving-image", "leftovers-image"]
int_cols = ["meal-id", "food-id", "nutrient-table-code", "food-group-code"]
float_cols = ["leftovers", "portion-size", "serving-size"]
date_cols = ["start-time", "submission-time"]

id_cols = ["patient", "visit", "meal-id", "food-id"]
df = df[id_cols + [col for col in df.columns if col not in id_cols]]

df = change_types(df, string_cols=string_cols + url_cols,
                  int_cols=int_cols,
                  float_cols=float_cols + [c for c in df.columns if c not in string_cols + bool_cols + url_cols + int_cols + date_cols],
                  date_cols=date_cols,
                  bool_cols=bool_cols)

test_data_frame(df)

units = {
    "energy": "kcal",
    "serving-size": "g or ml",
    "portion-size": "g or ml",
    "leftovers": "g or ml"
}
metadata = DataFrameMetadata(df, "1.3", column_units=units, comment="Intake 24, self reporting",
                             categorical_features=["visit", "diet", "food-amount", "meal-name", "intake-24-food-code", "food-group"])

save(metadata, "intake24")

print(df.columns)
print(df)
