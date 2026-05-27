from sqlalchemy import Column, String, JSON
from ..core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True) # Firebase UID
    display_name = Column(String)
    allergies = Column(JSON, default=[])
    conditions = Column(JSON, default=[])
    goals = Column(JSON, default=[])
