from typing import Union
import os
import logging
from fastapi import FastAPI
from route import router
from database import engine

import model

# CORS_ALLOW_ORIGINS = os.environ.get("CORS_ALLOW_ORIGINS", "*")
model.Base.metadata.create_all(bind=engine)

app = FastAPI()

logger = logging.getLogger(__name__)

app.include_router(router)
