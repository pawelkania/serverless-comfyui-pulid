import datetime
import json

from .container import image

with image.imports():
    from firebase_admin import credentials, initialize_app, storage, auth, exceptions

ResourceNotFound = exceptions.NotFoundError


class FirebaseAdmin:
    def __init__(self, service_account_json: str) -> None:
        service_account_info = json.loads(service_account_json)
        cred = credentials.Certificate(service_account_info)
        self.app = initialize_app(
            cred,
            options={"storageBucket": "wesmile-photobooth.appspot.com"},
        )
        self.bucket = storage.bucket(app=self.app)

    def sign_blob_url(self, blob_name: str, minutes: float) -> str:
        return self.bucket.blob(blob_name).generate_signed_url(
            expiration=datetime.timedelta(minutes), method="GET"
        )

    def download_bytes(self, blob_name: str):
        return self.bucket.blob(blob_name).download_as_bytes()

    def verify_token(self, token: str):
        try:
            auth.verify_id_token(app=self.app, id_token=token)
            return True
        except:
            return False
