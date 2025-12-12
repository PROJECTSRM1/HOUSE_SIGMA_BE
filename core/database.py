import os
import urllib.parse
from dotenv import load_dotenv # pyright: ignore[reportMissingImports]
from sqlalchemy import create_engine # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import sessionmaker, declarative_base # pyright: ignore[reportMissingImports]

load_dotenv()

HOST = os.getenv("DB_HOST", "127.0.0.1")
PORT = os.getenv("DB_PORT", "5432")
NAME = os.getenv("DB_NAME", "housesigma_dev")
USER = os.getenv("DB_USER", "postgres")
PASSWORD = os.getenv("DB_PASSWORD", "")

USER_ENC = urllib.parse.quote_plus(USER)
PASSWORD_ENC = urllib.parse.quote_plus(PASSWORD)

DATABASE_URL = f"postgresql+psycopg://{USER_ENC}:{PASSWORD_ENC}@{HOST}:{PORT}/{NAME}"

# ⚡ VERY FAST FAIL DB CONNECTION
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
    connect_args={
        "connect_timeout": 1  # fail in 1 second (you can set 0.5)
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    Returns DB session. If DB is DOWN → instantly return None.
    """
    try:
        db = SessionLocal()
        yield db
    except Exception as e:
        print("⚠ DB unavailable — fallback mode enabled:", e)
        yield None  # IMPORTANT
    finally:
        try:
            db.close()
        except:
            pass
