# from app.usecases.chat import chat, fetch_conversation, propose_conversation_title
import os
from fastapi import APIRouter, Request

from route_schema import (
    BotInput,
    BotOutput,
    ChatInput,
    ChatOutput,
)

from usecases.chat import chat

from embedding.main import main
from test import test

from usecases.bot import (
    create_new_bot
)

router = APIRouter()


@router.get("/")
def read_root():
    return {"Hello": "World"}


@router.post("/conversation")
def post_message(request: Request, chat_input: ChatInput):
    """Send chat message"""
    # return {"message": chat_input}
    # current_user: User = {"id": '1', "name": 'chaudhary'}

    output = chat(user_id='1', chat_input=chat_input)
    print(output, "output")
    return output

@router.post("/bot", response_model=BotOutput)
def post_bot(request: Request, bot_input: BotInput):
    """Create new private owned bot."""

    # current_user: User = request.state.current_user
    new_bot = create_new_bot('1', bot_input)
    source_urls = new_bot.knowledge.source_urls
    sitemap_urls = new_bot.knowledge.sitemap_urls
    filenames = new_bot.knowledge.filenames

    # main('1', new_bot.id, sitemap_urls, source_urls, filenames)
    test(new_bot.id, filenames[0])

    return new_bot
