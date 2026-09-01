from sqlalchemy import Column, Integer
from sqlalchemy.dialects.postgresql import INET
from database import Base


class UserLog(Base):
    __tablename__ = "user_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    ip_address = Column(INET, nullable=False, index=True)
