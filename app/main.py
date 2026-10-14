from fastapi import FastAPI
from app.controller.autenticacao import router as autenticacao_router

app = FastAPI()

app.include_router(autenticacao_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
