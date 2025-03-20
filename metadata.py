import pandas as pd
import json
import xml.etree.ElementTree as ET


class DataFrameMetadata:
    """
    Class to store metadata. Coded by ChatGPT with minor adjustments.

    Query: How can I generate metadata from a pandas dataframe - especially I am interested in values the number of
    rows, number of columns, column types, number of missing values, whether there are incomplete files and others
    which might be usable. I would like to also provide comments on some columns. Would that be possible. Finally,
    I would like to be able to save the data frame as it is and in csv, and the metadata in JSON and XML.

    What else should be in the metadata?
    """

    def __init__(self, df, version, column_comments=None, column_units=None, categorical_features=None, comment=""):
        self.df = df
        self.column_comments = column_comments if column_comments else {}
        self.column_units = column_units if column_units else {}
        self.categorical_features = categorical_features if categorical_features else []
        self.version = version
        self.comment = comment
        self.metadata = {}

    def generate_metadata(self):
        """Generate detailed metadata for the DataFrame"""
        metadata = {
            "num_rows": len(self.df),
            "num_columns": len(self.df.columns),
            "has_incomplete_rows": str(self.df.isna().any(axis=1).sum() > 0),
            "has_duplicates": str(self.df.duplicated().any()),
            "created_at": pd.Timestamp.now().isoformat(),
            "column_info": {},
            "version": self.version,
            "comment": self.comment,
            "data-source": "This data were measured under the CoDiet project. "
                           "The CoDiet project is co-funded by the European Union under Horizon Europe grant number "
                           "101084642. "
                           "CoDiet research activities taking place at Imperial College London and the University of "
                           "Nottingham are supported by UK Research and Innovation (UKRI) under the UK government’s "
                           "Horizon Europe funding guarantee [grant number 101084642]."
        }
        metadata.update(self.metadata)

        for col in self.df.columns:
            col_data = self.df[col]
            metadata["column_info"][col] = {
                "dtype": str(col_data.dtype),
                "num_missing": str(col_data.isna().sum()),
                "missing_percentage": str(round(col_data.isna().mean() * 100, 2)),
                "num_unique": str(col_data.nunique(dropna=True)),
                "unique_percentage": str(round(col_data.nunique(dropna=True) / len(col_data) * 100, 2)),
                "most_frequent_value": str(col_data.mode().iloc[0] if not col_data.mode().empty else None),
                "first_value": str(col_data.iloc[0] if not col_data.empty else None),
                "last_value": str(col_data.iloc[-1] if not col_data.empty else None),
            }
            if col in self.column_comments.keys():
                metadata["column_info"][col]["comment"] = self.column_comments.get(col)
            if col in self.column_units.keys():
                metadata["column_info"][col]["unit"] = self.column_units.get(col)

            if col_data.dtype.kind in "biufc":  # If column is numeric
                metadata["column_info"][col].update({
                    "mean": str(col_data.mean(skipna=True)),
                    "median": str(col_data.median(skipna=True)),
                    "min": str(col_data.min(skipna=True)),
                    "max": str(col_data.max(skipna=True)),
                    "std": str(col_data.std(skipna=True)),
                    "var": str(col_data.var(skipna=True)),
                })

            if col_data.dtype == "object" and col in self.categorical_features:  # If column is categorical
                metadata["column_info"][col]["categories"] = col_data.dropna().unique().tolist()

        return metadata

    def save_metadata_json(self, file_path):
        """Save metadata as JSON"""
        metadata = self.generate_metadata()
        print(metadata)
        with open(file_path, "w") as f:
            json.dump(metadata, f, indent=4)

    def save_metadata_xml(self, file_path):
        """Save metadata as XML"""
        metadata = self.generate_metadata()
        root = ET.Element("metadata")

        for key, value in metadata.items():
            if isinstance(value, dict):
                sub_element = ET.SubElement(root, key)
                for sub_key, sub_value in value.items():
                    column_element = ET.SubElement(sub_element, sub_key)
                    for k, v in sub_value.items():
                        sub_sub_element = ET.SubElement(column_element, k)
                        sub_sub_element.text = str(v)
            else:
                element = ET.SubElement(root, key)
                element.text = str(value)

        tree = ET.ElementTree(root)
        tree.write(file_path)
