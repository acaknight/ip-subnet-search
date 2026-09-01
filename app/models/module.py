from sqlalchemy import Column, Integer
from sqlalchemy.dialects.postgresql import INET
from app.db.database import Base


class UserLog(Base):
    __tablename__ = "user_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    ip_address = Column(INET, nullable=True, index=True)
