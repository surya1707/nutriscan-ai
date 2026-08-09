from sqlalchemy import Column, String, Integer, Float, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from ..core.database import Base

class ScanHistory(Base):
    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, index=True) # Linking to Firebase/User ID
    product_name = Column(String)
    brand = Column(String)
    health_score = Column(Integer)
    nova_group = Column(Integer)
    nutrients = Column(JSON)
    ingredients = Column(JSON)
    scanned_at = Column(DateTime(timezone=True), server_default=func.now())
