from metadata import DataFrameMetadata
from settings import Settings, SettingsKeys
import os


def save(dfm: DataFrameMetadata, name):
    csv_path = os.path.join(Settings().getdir(SettingsKeys.CLEANDIR), name + ".csv")
    pkl_path = os.path.join(Settings().getdir(SettingsKeys.CLEANDIR), name + ".pkl")
    xlsx_path = os.path.join(Settings().getdir(SettingsKeys.CLEANDIR), name + ".xlsx")

    dfm.df.to_csv(csv_path, index=False)
    dfm.df.to_pickle(pkl_path)
    dfm.df.to_excel(xlsx_path, index=False)

    dfm.metadata["csv_file_size"] = str(round(os.path.getsize(csv_path) / 1024))+"KB"
    dfm.metadata["pkl_file_size"] = str(round(os.path.getsize(pkl_path) / 1024))+"KB"
    dfm.metadata["xlsx_file_size"] = str(round(os.path.getsize(xlsx_path) / 1024))+"KB"
    dfm.metadata["file-name"] = name

    dfm.save_metadata_json(os.path.join(Settings().getdir(SettingsKeys.METADATADIR), name + ".json"))
    dfm.save_metadata_xml(os.path.join(Settings().getdir(SettingsKeys.METADATADIR), name + ".xml"))

