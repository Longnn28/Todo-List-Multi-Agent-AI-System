from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.apis.routers.vector_store_router import router as vector_store_router
from src.apis.routers.multi_agent_router import router as multi_agent_router
from src.config.pool_manager import database_lifespan, pool_manager
from src.utils.logger import logger

api_router = APIRouter()
api_router.include_router(vector_store_router)
api_router.include_router(multi_agent_router)

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # Startup
    logger.info("Application startup - Initializing resources...")
    async with database_lifespan():
        logger.info("Application startup complete")
        yield
    # Shutdown
    logger.info("Application shutdown complete")

def create_app():
    app = FastAPI(
        docs_url="/docs",
        title="AI Service",
        lifespan=app_lifespan
    )

    @app.get("/")
    def root():
        return {
            "message": "Backend is running"
        }

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app