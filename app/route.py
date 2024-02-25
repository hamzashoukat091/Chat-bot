from fastapi import APIRouter, Request
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from starlette import status
from sqlalchemy import and_
from fastapi.templating import Jinja2Templates
from chat import t5

from embedding import hugging

from route_schema import Bots as SchemaBots, Conversation as SchemaConversation
from model import Bots as ModelBots, Conversation as ModelConversation, Message as ModelMessage

router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/")
async def read_item(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"items": 'abc'}
    )

@router.get("/getChatBotResponse")
async def get_item(msg):
    return {"answer": "Model Not Ready"}

# @router.get("/")
# def read_root():
#     return {"Hello": "World"}


@router.post('/conversation')
async def post_message(con: SchemaConversation, db: Session = Depends(get_db)):
    # Check if the bot exists
    bot = db.query(ModelBots).filter(ModelBots.id == con.bot_id).first()
    if not bot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bot with id {con.bot_id} not found")

    # output = claude(chat_input=con)
    output = t5(chat_input=con)
    result = None
    if output:
        con_exist = db.query(ModelConversation).filter(and_(ModelConversation.id == con.conversation_id, ModelConversation.bot_id == con.bot_id)).first()
        if con_exist:
            message = ModelMessage(question=con.message.question, answer=output['answer'], model=con.message.model, conversation_id=con.conversation_id)
            db.add(message)
            db.commit()
            db.refresh(message)

            con_exist.message = {"id": message.id, "model": message.model, "question": message.question, "answer": message.answer}
            result = con_exist
        else:
            # Create a new conversation
            conversation = ModelConversation(last_message_id=con.last_message_id, title=con.title, bot_id=con.bot_id)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            message = ModelMessage(question=con.message.question, answer=output['answer'], model=con.message.model,
                                   conversation_id=conversation.id)
            db.add(message)
            db.commit()
            db.refresh(message)

            conversation.message = {"id": message.id, "model": message.model, "question": message.question, "answer": message.answer}
            result = conversation

    return result

@router.post('/bot', response_model=SchemaBots)
async def post_bot(bot: SchemaBots, db:Session = Depends(get_db)):
    bot_exist = db.query(ModelBots).filter(ModelBots.id == bot.id).first()
    if bot_exist:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The bot with id: {bot.id} already exists")
    latest_bot = db.query(ModelBots).order_by(ModelBots.id.desc()).first()
    if latest_bot and latest_bot.id + 1 != bot.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Use the bot id: {latest_bot.id + 1} to create new bots in order.")
    db_bot = ModelBots(title=bot.title, instruction=bot.instruction, description=bot.description, directory=bot.directory)
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    # cohere(bot.id, bot.directory)
    hugging(bot.id, bot.directory)
    return db_bot
