from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="DEX Local Block Builder")

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.get("/ping")
    async def ping() -> dict:
        return {"message": "pong"}

    return app
