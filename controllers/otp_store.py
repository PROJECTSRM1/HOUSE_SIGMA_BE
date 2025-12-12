import random
import time
from typing import Dict, Any

OTP_STORAGE: Dict[str, Dict[str, Any]] = {}
ACTIVE_EMAIL: str | None = None

OTP_LENGTH = 6
OTP_LIFETIME_SECONDS = 120


def generate_otp() -> str:
    return "".join(random.choices("0123456789", k=OTP_LENGTH))


def save_otp(email: str, otp: str):
    global ACTIVE_EMAIL
    ACTIVE_EMAIL = email

    OTP_STORAGE[email] = {
        "otp": otp,
        "expiry_time": time.time() + OTP_LIFETIME_SECONDS,
    }


def verify_otp(input_otp: str) -> str | None:
    """
    Verify OTP and return the email if OTP is valid.
    Return None if OTP invalid/expired.
    """
    global ACTIVE_EMAIL

    if ACTIVE_EMAIL is None:
        return None

    if ACTIVE_EMAIL not in OTP_STORAGE:
        return None

    stored = OTP_STORAGE[ACTIVE_EMAIL]

    # OTP expired
    if time.time() > stored["expiry_time"]:
        del OTP_STORAGE[ACTIVE_EMAIL]
        ACTIVE_EMAIL = None
        return None

    # Wrong OTP
    if stored["otp"] != input_otp:
        return None

    # Success
    email = ACTIVE_EMAIL
    del OTP_STORAGE[email]
    ACTIVE_EMAIL = None
    return email
