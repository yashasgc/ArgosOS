from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import files, documents, search, health
from app.config import settings

app = FastAPI(
    title="ArgosOS Backend",
    description="Intelligent file analysis and document management backend",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/v1", tags=["health"])
app.include_router(files.router, prefix="/v1", tags=["files"])
app.include_router(documents.router, prefix="/v1", tags=["documents"])
app.include_router(search.router, prefix="/v1", tags=["search"])

@app.get("/")
async def root():
    return {"message": "ArgosOS Backend API", "version": "1.0.0"}

