#region imports
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
#endregion 

# ------------------------
#   DB TABLE DEFINITIONS
# ------------------------

Base = declarative_base()

utcnow = lambda: datetime.now(timezone.utc)  

class Media(Base):
    __tablename__ = "media"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url_id = Column(String(12), nullable=False)
    
    file_name = Column(String(100), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    backend_url = Column(Text, nullable=False)
    key = Column(Text, nullable=False)
    created_on = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    delete_on = Column(DateTime(timezone=True), nullable=True)