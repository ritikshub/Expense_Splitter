from fastapi import FastAPI
from routes import router
import models
from database import Base, engine

app = FastAPI(title="Expense Splitter API")

models.Base.metadata.create_all(bind=engine)

app.include_router(router)


