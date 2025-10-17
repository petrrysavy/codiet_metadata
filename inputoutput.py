from metadata import DataFrameMetadata
from settings import Settings, SettingsKeys
import os


def save(dfm: DataFrameMetadata, name):
    csv_path = os.path.join(Settings().getdir(SettingsKeys.CLEANDIR), name + ".csv")
    pkl_path = os.path.join(Settings().getdir(SettingsKeys.CLEANDIR), name + ".pkl")
    xlsx_path = os.path.join(Settings().getdir(SettingsKeys.CLEANDIR), name + ".xlsx")
    parquet_path = os.path.join(Settings().getdir(SettingsKeys.CLEANDIR), name + ".parquet")
    feather_path = os.path.join(Settings().getdir(SettingsKeys.CLEANDIR), name + ".feather")

    duplicated_columns = dfm.df.columns.duplicated().any()

    dfm.df.to_csv(csv_path, index=False)
    dfm.df.to_pickle(pkl_path)
    xlsx_too_large = False
    try:
        dfm.df.to_excel(xlsx_path, index=False)
    except ValueError as e:
        xlsx_too_large = str(e).startswith("This sheet is too large!")
        print(e)
    if not duplicated_columns:
        dfm.df.to_parquet(parquet_path, engine="pyarrow")
        dfm.df.to_feather(feather_path)

    dfm.metadata["csv_file_size"] = str(round(os.path.getsize(csv_path) / 1024))+"KB"
    dfm.metadata["pkl_file_size"] = str(round(os.path.getsize(pkl_path) / 1024))+"KB"
    dfm.metadata["parquet_file_size"] = "Parquet does not support duplicate columns" if duplicated_columns else str(round(os.path.getsize(parquet_path) / 1024))+"KB"
    dfm.metadata["feather_file_size"] = "Feather does not support duplicate columns" if duplicated_columns else str(round(os.path.getsize(feather_path) / 1024))+"KB"
    dfm.metadata["xlsx_file_size"] =\
        "Too large for XLSX" if xlsx_too_large else str(round(os.path.getsize(xlsx_path) / 1024))+"KB"
    dfm.metadata["file-name"] = name

    dfm.save_metadata_json(os.path.join(Settings().getdir(SettingsKeys.METADATADIR), name + ".json"))
    dfm.save_metadata_xml(os.path.join(Settings().getdir(SettingsKeys.METADATADIR), name + ".xml"))

