# run: uvicorn app.main:app --reload

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import Settings, get_settings
from .database import Base, make_engine, make_session_factory
from .routers import content, students, teacher
from .seed import seed_content, seed_demo_class
from .services.llm import get_llm
from .services.tutor import NotFound


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    engine = make_engine(settings.database_url)
    session_factory = make_session_factory(engine)
    llm = get_llm(settings.llm_provider, api_key=settings.anthropic_api_key,
                  model=settings.anthropic_model)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Base.metadata.create_all(engine)
        with session_factory() as db:
            seed_content(db)
            if settings.seed_demo_data:
                seed_demo_class(db, llm)
        yield
        engine.dispose()

    app = FastAPI(title="MindLattice API", version="0.1.0", lifespan=lifespan,
                  description="Diagnoses *why* a student struggles by walking the knowledge graph.")
    app.state.session_factory = session_factory
    app.state.llm = llm

    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_methods=["*"], allow_headers=["*"])

    @app.exception_handler(NotFound)
    async def not_found(_: Request, error: NotFound):
        return JSONResponse(status_code=404, content={"detail": str(error)})

    @app.get("/api/health", tags=["meta"])
    def health():
        return {"status": "ok", "llm_provider": llm.name}

    app.include_router(content.router)
    app.include_router(students.router)
    app.include_router(teacher.router)
    return app


app = create_app()
