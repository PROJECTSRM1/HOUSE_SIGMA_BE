
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

# Load .env variables
load_dotenv()

SENDER_EMAIL = os.getenv("MAIL_FROM")
SENDER_PASSWORD = os.getenv("MAIL_PASSWORD")
SMTP_SERVER = os.getenv("MAIL_SERVER")
SMTP_PORT = int(os.getenv("MAIL_PORT", 587))


def send_otp_email(receiver_email: str, otp: str):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        raise ValueError("Email credentials not properly configured in .env")

    message = MIMEMultipart("alternative")
    message["Subject"] = "Your OTP Verification Code"
    message["From"] = SENDER_EMAIL
    message["To"] = receiver_email

    html = f"""
    <html>
    <body>
        <h2>Your OTP Code: <b>{otp}</b></h2>
        <p>This OTP is valid for 2 minutes.</p>
    </body>
    </html>
    """

    message.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver_email, message.as_string())
    except Exception as e:
        print("⚠️ Email send error:", e)
        raise RuntimeError("Failed to send OTP email")





# import resend
# import os

# # Load API key
# RESEND_API_KEY = os.getenv("RESEND_API_KEY")

# # Configure resend
# resend.api_key = RESEND_API_KEY


# def send_otp_email(receiver_email: str, otp: str):
#     if not RESEND_API_KEY:
#         raise ValueError("RESEND_API_KEY is not configured in Render environment variables")

#     try:
#         response = resend.Emails.send({
#             "from": "Rajashekar <onboarding@resend.dev>",
#             "to": [receiver_email],
#             "subject": "Your OTP Verification Code",
#             "html": f"""
#                 <html>
#                 <body>
#                     <h2>Your OTP Code: <b>{otp}</b></h2>
#                     <p>This OTP is valid for 2 minutes.</p>
#                 </body>
#                 </html>
#             """
#         })

#         print("📩 OTP email sent:", response)

#     except Exception as e:
#         print("⚠️ Email send failed:", e)
#         raise RuntimeError("Failed to send OTP email")
