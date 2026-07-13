from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="AI Inspection Validation Service",
    version="1.0.0",
    description="AI validation microservice for inspection platform",
)

app.include_router(router)