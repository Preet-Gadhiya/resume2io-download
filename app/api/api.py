import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Path, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.playwright_downloader import PlaywrightResumeDownloader

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")

# One Chromium process at a time — headless browsers are heavy
_semaphore = asyncio.Semaphore(1)


@router.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}


@router.post("/download/{doc_type}/{doc_id}")
async def download(
    doc_type: Annotated[str, Path(pattern="^(resume|cover_letter)$")],
    doc_id: Annotated[str, Path(pattern="^[0-9]+$")],
    x_session_id: Annotated[str, Header()],
    x_refresh_token: Annotated[str | None, Header()] = None,
):
    async with _semaphore:
        try:
            downloader = PlaywrightResumeDownloader(
                doc_id=doc_id,
                doc_type=doc_type,
                session_id=x_session_id,
                refresh_token=x_refresh_token or "",
            )
            pdf = await asyncio.to_thread(downloader.generate_pdf)
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("unexpected error during pdf generation")
            raise HTTPException(status_code=500, detail="Something went wrong. Please try again.") from e

    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{doc_type}_{doc_id}.pdf"'},
    )


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})
