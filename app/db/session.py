from sqlalchemy import create_engine, text
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


def run_migrations():
    """Add missing columns to existing tables (lightweight SQLite migration)."""
    migrations = [
        ("users", "password_hash", "ALTER TABLE users ADD COLUMN password_hash TEXT"),
        ("users", "created_at", "ALTER TABLE users ADD COLUMN created_at DATETIME"),
        ("provider_keys", "api_key_encrypted", "ALTER TABLE provider_keys ADD COLUMN api_key_encrypted TEXT"),
        ("provider_keys", "created_at", "ALTER TABLE provider_keys ADD COLUMN created_at DATETIME"),
        ("prompts", "user_id", "ALTER TABLE prompts ADD COLUMN user_id INTEGER REFERENCES users(id)"),
        ("provider_keys", "status", "ALTER TABLE provider_keys ADD COLUMN status TEXT DEFAULT 'pending'"),
        ("provider_keys", "validated_at", "ALTER TABLE provider_keys ADD COLUMN validated_at DATETIME"),
        ("provider_keys", "discovered_models", "ALTER TABLE provider_keys ADD COLUMN discovered_models JSON"),
    ]
    with engine.connect() as conn:
        for table, column, sql in migrations:
            result = conn.execute(text(f"PRAGMA table_info({table})"))
            columns = {row[1] for row in result}
            if column not in columns:
                conn.execute(text(sql))
                conn.commit()
