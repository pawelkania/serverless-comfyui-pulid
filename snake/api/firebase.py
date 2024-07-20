import datetime
import json

from snake.api.image import image

with image.imports():
    from firebase_admin import credentials, initialize_app, storage


class FirebaseAdmin:
    def __init__(self, service_account_json: str) -> None:
        service_account_info = json.loads(service_account_json)
        cred = credentials.Certificate(service_account_info)
        firebase_app = initialize_app(
            cred,
            options={"storageBucket": "wesmile-photobooth.appspot.com"},
        )
        self.bucket = storage.bucket(app=firebase_app)

    def sign_blob_url(self, blob_name: str, minutes: float) -> str:
        return self.bucket.blob(blob_name).generate_signed_url(
            expiration=datetime.timedelta(minutes), method="GET"
        )
