from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.controller.autenticacao import router as autenticacao_router
from app.controller.mensagens import router as mensagens_router

app = FastAPI()
app.add_middleware(CORSMiddleware,
                   allow_origins="*",
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"],
                   )

app.include_router(autenticacao_router)
app.include_router(mensagens_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health", status_code=status.HTTP_200_OK)
async def health():
    return {}
