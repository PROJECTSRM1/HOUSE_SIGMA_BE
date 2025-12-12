from sqlalchemy import Column, Integer, String, Boolean, BigInteger, TIMESTAMP # pyright: ignore[reportMissingImports]
from core.database import Base # pyright: ignore[reportMissingImports]
from datetime import datetime

class UserRegistration(Base):
    __tablename__ = "user_registration"

    id = Column(BigInteger, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)

    # Google users have no password — so make nullable=True
    password = Column(String(500), nullable=True)

    mobile = Column(String(15), nullable=True)
    city_id = Column(Integer, nullable=True)
    role_id = Column(Integer, nullable=True)

    created_by = Column(BigInteger, nullable=True)
    created_date = Column(TIMESTAMP, default=datetime.utcnow, nullable=True)

    modified_by = Column(BigInteger, nullable=True)
    modified_date = Column(TIMESTAMP, nullable=True)

    is_active = Column(Boolean, default=True)
