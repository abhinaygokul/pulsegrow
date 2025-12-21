from fastapi import FastAPI
from backend.database import engine, Base
import backend.models.models # Import models so they are registered with Base

# Create tables
Base.metadata.create_all(bind=engine)

from backend.api import endpoints

app = FastAPI(title="PulseGrow API", version="1.0.0")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to PulseGrow API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
