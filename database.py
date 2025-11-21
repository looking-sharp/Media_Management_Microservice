from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from contextlib import contextmanager
from flask import jsonify
from datetime import datetime, timedelta
import os
import secrets

from models import Base, Media # Import from models.py

# ------------------------
#   ENV + ENGINE SETUP
# ------------------------

load_dotenv()
DELETE_AFTER_DAYS = 7

# Path setup
basedir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.dirname(basedir)
db_filename = "media.db"

# Full absolute path to the database inside the container
default_db_path = os.path.join(parent_dir, "data", db_filename)
print(default_db_path)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{default_db_path}")

# Ensure folder exists
os.makedirs(os.path.dirname(default_db_path), exist_ok=True)

# Database engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# Create session 
SessionLocal = sessionmaker(
    bind=engine, 
    autocommit=False, 
    autoflush=False
)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db() -> Session:
    """
    Return a new database session.
    Use `with get_db() as db:` to close automatically
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_url_id(session: Session, length: int = 12) -> str:
    """Create short for URL"""
    _id = secrets.token_urlsafe(length)[:length]
    while session.query(Media).filter(Media.url_id == _id).first() is not None:
        _id = secrets.token_urlsafe(length)[:length]
    return _id

def add_to_db(session, instance, return_bool=False):
    """
    Add and commit a new record to the database.

    Returns:
        If return_bool=True: (bool): True on success, False on failure.
        Else: (instance) returns the instance.
    """
    try:
        session.add(instance)
        session.commit()
        session.refresh(instance)
        return True if return_bool else instance
    except Exception as e:
        session.rollback()
        if return_bool:
            return False
        raise e

def add_image_to_db(image_id, file_name, mime_type, file_size, backend_url):
    with get_db() as db:
        url_id = create_url_id(db)
        new_media = Media (
            id = image_id,
            url_id = url_id,
            file_name = file_name,
            mime_type = mime_type,
            file_size = file_size,
            backend_url = backend_url
        )

        db.add(new_media)
        db.commit()

        return jsonify({"message": "success", 
                        "id": image_id, 
                        "url_id": url_id,
                        "file_name": file_name,
                        "mime_type": mime_type,
                        "file_size": file_size}), 200