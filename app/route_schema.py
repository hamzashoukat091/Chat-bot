# build a schema using pydantic
from pydantic import BaseModel
from typing import Optional, Dict, List


class Bots(BaseModel):
    id: int
    title: str
    instruction: str
    description: str
    directory: str

    class Config:
        orm_mode = True


class Message(BaseModel):
    question: str
    model: str

    class Config:
        orm_mode = True


class Conversation(BaseModel):
    conversation_id: int
    title: str
    last_message_id: str
    bot_id: int
    message: Message

    class Config:
        orm_mode = True
