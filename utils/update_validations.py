import re
from fastapi import HTTPException, status
from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]
from models.user_model import UserRegistration

GMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@gmail\.com$"


def validate_email_format(email: str):
    """Ensure email is a valid Gmail address."""
    if not re.match(GMAIL_REGEX, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email. Only Gmail addresses (example@gmail.com) allowed."
        )


def check_email_exists_db(email: str, db: Session):
    """Check if email already exists in PostgreSQL DB."""
    user = db.query(UserRegistration).filter(
        UserRegistration.email == email.lower()
    ).first()

    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered. Please login instead."
        )


def validate_password(password: str):
    """Validate password strength."""
    if len(password) > 72:
        raise HTTPException(400, "Password cannot exceed 72 characters.")

    if len(password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters long.")

    if not re.search(r"[A-Za-z]", password):
        raise HTTPException(400, "Password must contain at least 1 letter.")

    if not re.search(r"[0-9]", password):
        raise HTTPException(400, "Password must contain at least 1 number.")

    if not re.search(r"[!@#$%^&*?_]", password):
        raise HTTPException(
            400,
            "Password must contain at least 1 special character (!@#$%^&*?_)."
        )
