from typing import Optional

from google.cloud import firestore
from google.oauth2.service_account import Credentials as ServiceAccountCredentials  # type: ignore


class NotConnectedException(Exception):
    pass


class FirestoreConnection:
    _instance: Optional['FirestoreConnection'] = None
    db: Optional[firestore.Client] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.db = None  # デフォルトではdbオブジェクトはNoneとして初期化
        return cls._instance

    def initialize(self, project_id: Optional[str] = None, service_account_key_path: Optional[str] = None):
        if self.db is None:
            if service_account_key_path:
                creds = ServiceAccountCredentials.from_service_account_file(service_account_key_path)
                self.db = firestore.Client(credentials=creds, project=project_id)
            else:
                self.db = firestore.Client(project=project_id)

    def set_db(self, db):
        self.db = db

    def collection(self, collection_name):
        if self.db is None:
            raise NotConnectedException("FirestoreConnection is not initialized. Call initialize() first.")
        return self.db.collection(collection_name)


# global singleton instance
conn = FirestoreConnection()
