# build a schema using pydantic
from pydantic import BaseModel


class Bots(BaseModel):
    id: int
    title: str
    instruction: str
    description: str
    directory: str

    class Config:
        orm_mode = True
