from fastapi import APIRouter, HTTPException, Depends # pyright: ignore[reportMissingImports]
from fastapi.responses import RedirectResponse # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]
import os
import requests # pyright: ignore[reportMissingModuleSource]

from services.google_service import verify_google_token
from utils.jwt_handler import create_access_token, create_refresh_token
from core.database import get_db
from models.user_model import UserRegistration

router = APIRouter(prefix="/api/auth", tags=["Google Auth"])

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Update to your backend URL if deployed
REDIRECT_URI = "http://127.0.0.1:8000/api/auth/google/callback"


# --------------------------------------------------------------
# STEP 1: Redirect user to Google Login Screen
# --------------------------------------------------------------
@router.get("/google/login")
async def google_login():
    google_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        "?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={requests.utils.quote(REDIRECT_URI, safe='')}"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
        "&prompt=select_account"
    )
    return RedirectResponse(google_url)


# --------------------------------------------------------------
# STEP 2: Google redirects back with "code"
# --------------------------------------------------------------
@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):

    # Exchange authorization code for tokens
    token_url = "https://oauth2.googleapis.com/token"

    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    token_res = requests.post(token_url, data=data).json()

    if "id_token" not in token_res:
        raise HTTPException(400, "Unable to fetch Google ID token")

    id_token = token_res["id_token"]

    # Verify ID token
    google_data = verify_google_token(id_token)
    if not google_data:
        raise HTTPException(401, "Invalid Google token")

    email = google_data.get("email")
    name = google_data.get("name")
    picture = google_data.get("picture")

    if not email:
        raise HTTPException(400, "Google account has no email")

    payload = {"email": email, "name": name, "picture": picture}

    # Check if user exists in DB
    user = db.query(UserRegistration).filter(UserRegistration.email == email).first()

    if not user:
        user = UserRegistration(
            full_name=name,
            email=email,
            password="",  # Social login has no password
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Generate JWT tokens
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    # Redirect back to frontend with tokens
    frontend_url = (
        "http://localhost:8080/google-auth-success"
        f"?access_token={access_token}"
        f"&refresh_token={refresh_token}"
        f"&name={name}"
        f"&email={email}"
        f"&picture={picture}"
    )

    return RedirectResponse(frontend_url)
