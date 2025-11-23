from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from app.api import endpoints, settings as settings_api
from app.core.config import settings
from app.services.detector import streamer
from app.core.database import create_db_and_tables
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    yield
    # Shutdown
    streamer.stop()

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include API router
app.include_router(endpoints.router, prefix="/api")
app.include_router(settings_api.router, prefix="/api/settings", tags=["settings"])

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request, "title": settings.PROJECT_NAME})

@app.get("/dashboard")
def read_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "title": settings.PROJECT_NAME + " - Dashboard"})

@app.get("/settings")
def read_settings(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request, "title": settings.PROJECT_NAME + " - Settings"})

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
