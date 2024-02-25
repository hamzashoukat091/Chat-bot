from typing import Union
import os
import logging
from fastapi import FastAPI
from route import router
from database import engine
from fastapi.staticfiles import StaticFiles

import model

# CORS_ALLOW_ORIGINS = os.environ.get("CORS_ALLOW_ORIGINS", "*")
model.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

logger = logging.getLogger(__name__)

app.include_router(router)
