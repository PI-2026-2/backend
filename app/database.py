from typing import Annotated
from dotenv import dotenv_values
from fastapi import Depends
from sqlmodel import Session, create_engine
from .model.tables import *
from .model.enums import *

config = dotenv_values(".env")
DATABASE_URL = config["DATABASE_URL"]
assert DATABASE_URL != None

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, echo=True, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
