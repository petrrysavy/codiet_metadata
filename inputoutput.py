from metadata import DataFrameMetadata
from settings import Settings, SettingsKeys
import os


def save(dfm: DataFrameMetadata, name):
    print(os.path.join(Settings().getdir(SettingsKeys.CLEANDIR), name + ".csv"))
    dfm.df.to_csv(os.path.join(Settings().getdir(SettingsKeys.CLEANDIR), name + ".csv"), index=False)
    dfm.df.to_pickle(os.path.join(Settings().getdir(SettingsKeys.CLEANDIR), name + ".pkl"))
    dfm.df.to_excel(os.path.join(Settings().getdir(SettingsKeys.CLEANDIR), name + ".xlsx"), index=False)

    dfm.save_metadata_json(os.path.join(Settings().getdir(SettingsKeys.METADATADIR), name + ".json"))
    dfm.save_metadata_xml(os.path.join(Settings().getdir(SettingsKeys.METADATADIR), name + ".xml"))

