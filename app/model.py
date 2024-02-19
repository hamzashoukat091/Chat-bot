from database import Base
from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean, text


class Bots(Base):
    __tablename__ = "bots"

    id = Column(Integer,primary_key=True,nullable=False)
    title = Column(String,nullable=True)
    instruction = Column(String,nullable=True)
    description = Column(String, nullable=True)
    directory = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
