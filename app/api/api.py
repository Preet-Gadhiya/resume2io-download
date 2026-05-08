from typing import Annotated

from fastapi import APIRouter, Header, Path, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.playwright_downloader import PlaywrightResumeDownloader

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/download/{resume_id}")
def download_resume(
    resume_id: Annotated[str, Path(pattern="^[0-9]+$")],
    x_session_id: Annotated[str, Header()],
    x_refresh_token: Annotated[str | None, Header()] = None,
):
    downloader = PlaywrightResumeDownloader(
        resume_id=resume_id,
        session_id=x_session_id,
        refresh_token=x_refresh_token or "",
    )
    return Response(
        downloader.generate_pdf(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{resume_id}.pdf"'},
    )


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})
