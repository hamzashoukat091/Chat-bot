from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Float, Integer, String, TIMESTAMP, Boolean, text


class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    last_message_id = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    bot_id = Column(Integer, ForeignKey('bots.id'))

    # Define one-to-many relationship with Message
    # message = relationship("Message", back_populates="conversation")


class Bots(Base):
    __tablename__ = "bots"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    instruction = Column(String, nullable=True)
    description = Column(String, nullable=True)
    directory = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    # Define one-to-many relationship with Conversation
    # conversation = relationship("Conversation", back_populates="bot")


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String)
    answer = Column(String)
    model = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    # Define many-to-one relationship with Conversation
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    # conversation = relationship("Conversation", back_populates="messages")