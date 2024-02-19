# from app.usecases.chat import chat, fetch_conversation, propose_conversation_title
from fastapi import APIRouter, Request
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from starlette import status

from usecases.chat import chat

from test import test


from route_schema import Bots as SchemaBots
from model import Bots as ModelBots

from usecases.bot import (
    create_new_bot
)

router = APIRouter()


@router.get("/")
def read_root():
    return {"Hello": "World"}


@router.post("/conversation")
def post_message(request: Request, chat_input):
    """Send chat message"""
    # return {"message": chat_input}
    # current_user: User = {"id": '1', "name": 'chaudhary'}

    output = chat(user_id='1', chat_input=chat_input)
    print(output, "output")
    return output


@router.post('/bot', response_model=SchemaBots)
async def post_bot(bot: SchemaBots, db:Session = Depends(get_db)):
    bot_exist = db.query(ModelBots).filter(ModelBots.id == bot.id).first()
    if bot_exist:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The bot with id: {bot.id} already exists")

    db_bot = ModelBots(title=bot.title, instruction=bot.instruction, description=bot.description, directory=bot.directory)
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    test(bot.id, bot.directory)
    return db_bot


# @router.post("/bot")
# def post_bot(request: Request, bot_input):
#     """Create new private owned bot."""
#
#     # current_user: User = request.state.current_user
#     new_bot = create_new_bot('1', bot_input)
#     source_urls = new_bot.knowledge.source_urls
#     sitemap_urls = new_bot.knowledge.sitemap_urls
#     filenames = new_bot.knowledge.filenames
#
#     # main('1', new_bot.id, sitemap_urls, source_urls, filenames)
#     test(new_bot.id, filenames)
#
#     return new_bot
