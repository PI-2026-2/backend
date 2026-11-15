from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controller.autenticacao import router as autenticacao_router
from app.controller.integration import router as integration_router

app = FastAPI()
app.add_middleware(CORSMiddleware,
                   allow_origins="*",
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"],
                   )

app.include_router(autenticacao_router)
app.include_router(integration_router)



@app.get("/")
async def root():
    return {"message": "Hello World"}
