import io
import logging
from dataclasses import dataclass, field

from fastapi import HTTPException
from PIL import Image
from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

logger = logging.getLogger(__name__)

_OVERLAY_SELECTORS = [
    "[data-testid='preview-pagination-container']",
    "[data-testid='preview-customize-button-container']",
]

_EDITOR_PATHS = {
    "resume": "resumes",
    "cover_letter": "cover-letters",
}


@dataclass
class PlaywrightResumeDownloader:
    doc_id: str
    session_id: str
    doc_type: str = "resume"
    refresh_token: str = ""

    def __post_init__(self) -> None:
        if self.doc_type not in _EDITOR_PATHS:
            raise HTTPException(status_code=400, detail=f"doc_type must be one of: {list(_EDITOR_PATHS)}")

    def generate_pdf(self) -> bytes:
        path = _EDITOR_PATHS[self.doc_type]
        url = f"https://resume.io/app/{path}/{self.doc_id}/edit"
        logger.info("starting pdf generation doc_id=%s type=%s", self.doc_id, self.doc_type)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                return self._run(browser, url)
            finally:
                browser.close()

    def _run(self, browser, url: str) -> bytes:
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/147.0.0.0 Safari/537.36"
            ),
            device_scale_factor=2,
        )
        self._inject_cookies(context)

        page = context.new_page()
        page.goto(url, wait_until="networkidle", timeout=45000)

        if "/sign-in" in page.url or "/login" in page.url:
            raise HTTPException(status_code=401, detail="Session cookie is invalid or expired")

        page.wait_for_selector("[data-testid='preview-canvas-primary']", timeout=20000)
        page.wait_for_function(
            "() => { const c = document.querySelector('[data-testid=\"preview-canvas-primary\"]'); "
            "return c && c.width > 0 && c.height > 0; }",
            timeout=20000,
        )
        page.wait_for_load_state("networkidle", timeout=15000)
        page.wait_for_timeout(3000)

        total_pages = self._get_total_pages(page)
        logger.info("doc_id=%s total_pages=%d", self.doc_id, total_pages)

        page_images = []
        for page_num in range(1, total_pages + 1):
            if page_num > 1:
                # click next once from the current page, then wait for canvas to repaint
                page.click("[data-testid='preview-next-page-button']")
                page.wait_for_timeout(2500)

            logger.info("capturing page %d/%d", page_num, total_pages)
            page_images.append(self._capture_canvas(page))

        return self._build_pdf(page_images)

    def _inject_cookies(self, context) -> None:
        cookies = [
            {
                "name": "_session_id",
                "value": self.session_id,
                "domain": "resume.io",
                "path": "/",
                "secure": True,
                "httpOnly": True,
                "sameSite": "Lax",
            }
        ]
        if self.refresh_token:
            cookies.append(
                {
                    "name": "api_auth_refresh_token",
                    "value": self.refresh_token,
                    "domain": "resume.io",
                    "path": "/api",
                    "secure": True,
                    "httpOnly": True,
                    "sameSite": "Strict",
                }
            )
        context.add_cookies(cookies)

    def _get_total_pages(self, page) -> int:
        try:
            text = page.text_content("[data-testid='preview-page-counter']", timeout=5000)
            parts = text.strip().split("/")
            if len(parts) == 2:
                return int(parts[1].strip())
        except Exception:
            pass
        return 1

    def _capture_canvas(self, page) -> bytes:
        element = page.query_selector("[data-testid='preview-canvas-primary']")
        if not element:
            raise HTTPException(status_code=500, detail="Canvas not found. The resume may not have loaded.")

        page.evaluate(
            "(selectors) => selectors.forEach(s => { const el = document.querySelector(s); if (el) el.style.visibility = 'hidden'; })",
            _OVERLAY_SELECTORS,
        )
        try:
            return element.screenshot(type="png")
        finally:
            page.evaluate(
                "(selectors) => selectors.forEach(s => { const el = document.querySelector(s); if (el) el.style.visibility = ''; })",
                _OVERLAY_SELECTORS,
            )

    def _build_pdf(self, page_images: list[bytes]) -> bytes:
        pdf_writer = PdfWriter()
        for img_bytes in page_images:
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            pdf_buf = io.BytesIO()
            img.save(pdf_buf, format="PDF", resolution=300)
            pdf_buf.seek(0)
            pdf_writer.add_page(PdfReader(pdf_buf).pages[0])

        out = io.BytesIO()
        pdf_writer.write(out)
        logger.info("pdf built pages=%d size=%d bytes", len(page_images), out.tell())
        return out.getvalue()
