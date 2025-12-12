from google.oauth2 import id_token # pyright: ignore[reportMissingImports]
from google.auth.transport import requests # pyright: ignore[reportMissingImports]
import os
from dotenv import load_dotenv # pyright: ignore[reportMissingImports]

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


def verify_google_token(token: str):
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )
        return idinfo

    except Exception as e:
        print("Google token error:", e)
        return None
