from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# SQLite local file
DATABASE_URL = "sqlite:///./byok.db"

# For SQLite, check_same_thread must be False when used in FastAPI
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
