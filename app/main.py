import logging

import uvicorn
from fastapi import FastAPI

from app.api.api import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="resume2io-download",
    description="Download resume.io documents as PDF",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
