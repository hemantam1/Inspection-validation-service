from fastapi import FastAPI

from app.api.routes import router
from app.database.connection import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Inspection Validation Service",
    version="1.0.0",
    description="AI validation microservice for inspection platform",
)

app.include_router(router)