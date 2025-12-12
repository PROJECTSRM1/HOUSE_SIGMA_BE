from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class EmailRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class OTPVerify(BaseModel):
    otp: str

class MessageResponse(BaseModel):
    message: str
    status: Optional[str] = "success"

class LoginRequest(BaseModel):
    username_or_email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ForgotPasswordOTPVerify(BaseModel):
    email: EmailStr
    otp: str
    new_password: str


