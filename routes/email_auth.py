from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form # pyright: ignore[reportMissingImports]
import os
from datetime import datetime
from passlib.context import CryptContext # pyright: ignore[reportMissingModuleSource]
from sqlalchemy.orm import Session  # pyright: ignore[reportMissingImports]

from models.email_verify_schema import (
    EmailRequest,
    ForgotPasswordOTPVerify,
    ForgotPasswordRequest,
    OTPVerify,
    MessageResponse,
    LoginRequest
)

from models.user_model import UserRegistration
from core.database import get_db
from controllers.otp_store import generate_otp, save_otp, verify_otp
from services.otp_service import send_otp_email
from utils.validations import validate_email_format, validate_password
from utils.jwt_handler import create_access_token, create_refresh_token, verify_token


# ----------------------------------------------------------
# PASSWORD HASHING (FIXED - no bcrypt issues on Windows)
# ----------------------------------------------------------

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)


BASE_DIR = "app/static"
ALLOWED_FOLDERS = ["users", "documents", "photos", "avatars", "camera_uploads"]

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def get_profile_image(email: str):
    safe_email = email.replace("@", "_").replace(".", "_").lower()

    for folder in ALLOWED_FOLDERS:
        path = f"{BASE_DIR}/{folder}/{safe_email}.jpg"
        if os.path.exists(path):
            return f"http://localhost:8000/static/{folder}/{safe_email}.jpg"

    return "http://localhost:8000/static/users/default.png"


# ----------------------------------------------------------
# SIGNUP — Send OTP
# ----------------------------------------------------------

@router.post("/sign", response_model=MessageResponse)
async def request_otp(request: EmailRequest, db: Session = Depends(get_db)):

    name = request.name.strip()
    email = request.email.lower().strip()
    password = request.password.strip()

    validate_email_format(email)
    validate_password(password)

    existing = db.query(UserRegistration).filter(UserRegistration.email == email).first()
    if existing:
        raise HTTPException(400, "Email already registered")

    hashed_pwd = hash_password(password)

    temp_user = UserRegistration(
        full_name=name,
        email=email,
        password=hashed_pwd,
        role_id=1,
        is_active=False,
        created_by=None,
        created_date=datetime.utcnow()
    )

    db.add(temp_user)
    db.commit()

    otp = generate_otp()
    save_otp(email, otp)
    send_otp_email(email, otp)

    return MessageResponse(
        message="OTP sent successfully!",
        status="pending_verification"
    )


# ----------------------------------------------------------
# SIGNUP — Verify OTP
# ----------------------------------------------------------

@router.post("/sign/otp", response_model=MessageResponse)
async def verify_otp_endpoint(request: OTPVerify, db: Session = Depends(get_db)):

    email = verify_otp(request.otp)
    if not email:
        raise HTTPException(400, "Invalid or expired OTP")

    user = db.query(UserRegistration).filter(
        UserRegistration.email == email
    ).first()

    if not user:
        raise HTTPException(400, "Signup not found")

    user.is_active = True
    db.commit()

    return MessageResponse(
        message="User registered successfully!",
        status="verified"
    )


# ----------------------------------------------------------
# NORMAL LOGIN
# ----------------------------------------------------------

@router.post("/login")
async def login_user(request: LoginRequest, db: Session = Depends(get_db)):

    username = request.username_or_email.strip().lower()
    password = request.password.strip()

    user = db.query(UserRegistration).filter(
        (UserRegistration.email == username) |
        (UserRegistration.full_name == username)
    ).first()

    if not user:
        raise HTTPException(400, "User not found")

    if not user.is_active:
        raise HTTPException(400, "Your account is not verified yet")

    if not verify_password(password, user.password):
        raise HTTPException(400, "Invalid password")

    access_token = create_access_token({"id": user.id, "email": user.email})
    refresh_token = create_refresh_token({"id": user.id, "email": user.email})

    profile_image_url = get_profile_image(user.email)

    return {
        "message": "Login successful",
        "status": "success",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.full_name,
            "email": user.email,
            "profile_image": profile_image_url
        }
    }


# ----------------------------------------------------------
# UPLOAD PROFILE IMAGE
# ----------------------------------------------------------

@router.post("/upload-image")
async def upload_image(
    email: str = Form(...),
    folder: str = Form(...),
    image: UploadFile = File(...)
):
    folder = folder.strip()

    if folder not in ALLOWED_FOLDERS:
        raise HTTPException(400, f"Invalid folder. Allowed: {ALLOWED_FOLDERS}")

    upload_path = os.path.join(BASE_DIR, folder)
    os.makedirs(upload_path, exist_ok=True)

    safe_email = email.replace("@", "_").replace(".", "_").lower()
    filename = f"{safe_email}.jpg"

    file_path = os.path.join(upload_path, filename)

    with open(file_path, "wb") as f:
        f.write(await image.read())

    return {
        "status": "success",
        "message": "Image uploaded",
        "image_url": f"http://localhost:8000/static/{folder}/{filename}"
    }


# ----------------------------------------------------------
# FORGOT PASSWORD — SEND OTP
# ----------------------------------------------------------

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):

    email = request.email.lower().strip()

    user = db.query(UserRegistration).filter(UserRegistration.email == email).first()
    if not user:
        raise HTTPException(400, "Email not registered")

    otp = generate_otp()
    save_otp(email, otp)
    send_otp_email(email, otp)

    return MessageResponse(
        message="Password reset OTP sent",
        status="otp_sent"
    )


# ----------------------------------------------------------
# FORGOT PASSWORD — VERIFY OTP + RESET PASSWORD
# ----------------------------------------------------------

@router.post("/forgot-password/verify", response_model=MessageResponse)
async def forgot_password_verify(request: ForgotPasswordOTPVerify, db: Session = Depends(get_db)):

    email = request.email.lower().strip()

    verified = verify_otp(request.otp)
    if verified != email:
        raise HTTPException(400, "Invalid OTP")

    user = db.query(UserRegistration).filter(UserRegistration.email == email).first()
    if not user:
        raise HTTPException(400, "User not found")

    if verify_password(request.new_password, user.password):
        raise HTTPException(400, "New password cannot be same as old password")

    user.password = hash_password(request.new_password)
    db.commit()

    return MessageResponse(
        message="Password reset successful",
        status="password_reset"
    )


# ----------------------------------------------------------
# LOGOUT
# ----------------------------------------------------------

@router.post("/logout")
async def logout_user(username_or_email: str, db: Session = Depends(get_db)):

    username_or_email = username_or_email.lower().strip()

    user = db.query(UserRegistration).filter(
        (UserRegistration.email == username_or_email) |
        (UserRegistration.full_name == username_or_email)
    ).first()

    if not user:
        raise HTTPException(404, "User not found")

    user.modified_date = datetime.utcnow()
    db.commit()

    return {"message": "Logout successful", "status": "logged_out"}


# ----------------------------------------------------------
# GET ALL USERS
# ----------------------------------------------------------

@router.get("/users")
async def get_all_users(db: Session = Depends(get_db)):
    users = db.query(UserRegistration).all()

    return {
        "total": len(users),
        "users": [
            {
                "id": u.id,
                "name": u.full_name,
                "email": u.email,
                "is_active": u.is_active,
                "created_date": u.created_date
            }
            for u in users
        ]
    }


# ----------------------------------------------------------
# GET USER BY ID
# ----------------------------------------------------------

@router.get("/users/{user_id}")
async def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserRegistration).filter(UserRegistration.id == user_id).first()

    if not user:
        raise HTTPException(404, "User not found")

    return {
        "id": user.id,
        "name": user.full_name,
        "email": user.email,
        "mobile": user.mobile,
        "city_id": user.city_id,
        "role_id": user.role_id,
        "is_active": user.is_active,
        "created_date": user.created_date,
        "modified_date": user.modified_date
    }


# ----------------------------------------------------------
# DELETE USER
# ----------------------------------------------------------

@router.delete("/delete-user")
async def delete_user(username_or_email: str, db: Session = Depends(get_db)):
    username_or_email = username_or_email.lower().strip()

    user = db.query(UserRegistration).filter(
        (UserRegistration.email == username_or_email) |
        (UserRegistration.full_name == username_or_email)
    ).first()

    if not user:
        raise HTTPException(404, "User not found")

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully", "status": "user_deleted"}


# ----------------------------------------------------------
# AUTHENTICATED USER
# ----------------------------------------------------------

@router.get("/me")
def get_current_user(user=Depends(verify_token)):
    return {
        "message": "Authenticated user",
        "user": user
    }
