from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from config import get_settings  # noqa: E402
from api import analyze, backtest, market, history  # noqa: E402

app = FastAPI(title="Sistema BVL API", version="2.0.0", docs_url="/docs")

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router, prefix="/api")
app.include_router(backtest.router, prefix="/api")
app.include_router(market.router,   prefix="/api")
app.include_router(history.router,  prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
