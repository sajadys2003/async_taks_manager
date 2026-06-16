from sqlalchemy import Column, Integer, String, Enum
from app.models.job import Base  # We share the same Base as the Job model
from app.models.enums import UserRole

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)