import os
from enum import Enum


class SettingsKeys(Enum):
    BASEDIR = "basedir"
    RAWDIR = "rawdir"
    CLEANDIR = "cleaned"
    METADATADIR = "metadata"


class Settings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.config = {}
            self.config[SettingsKeys.BASEDIR] = os.path.join("C:\\", "Users", "petrr", "Documents", "codiet", "data")
            self.config[SettingsKeys.RAWDIR] = "raw"
            self.config[SettingsKeys.CLEANDIR] = "cleaned"
            self.config[SettingsKeys.METADATADIR] = "metadata"
            self._initialized = True

    def set(self, key: SettingsKeys, value):
        self.config[key] = value

    def get(self, key: SettingsKeys, default=None):
        return self.config.get(key, default)

    def getdir(self, key: SettingsKeys):
        return os.path.join(self.get(SettingsKeys.BASEDIR), self.get(key))
