import io
from dataclasses import dataclass

from fastapi import HTTPException
from PIL import Image
from playwright.sync_api import sync_playwright
from pypdf import PdfWriter


@dataclass
class PlaywrightResumeDownloader:
    resume_id: str
    session_id: str
    refresh_token: str = ""

    def generate_pdf(self) -> bytes:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                return self._run(browser)
            finally:
                browser.close()

    def _run(self, browser) -> bytes:
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
        page.goto(
            f"https://resume.io/app/resumes/{self.resume_id}/edit",
            wait_until="networkidle",
            timeout=45000,
        )

        if "/sign-in" in page.url or "/login" in page.url:
            raise HTTPException(status_code=401, detail="Session cookie is invalid or expired")

        # Wait for primary canvas to be painted and fonts to settle
        page.wait_for_selector("[data-testid='preview-canvas-primary']", timeout=20000)
        page.wait_for_function(
            "() => { const c = document.querySelector('[data-testid=\"preview-canvas-primary\"]'); "
            "return c && c.width > 0 && c.height > 0; }",
            timeout=20000,
        )
        # Wait for network fonts to finish loading then extra settle time for canvas render
        page.wait_for_load_state("networkidle", timeout=15000)
        page.wait_for_timeout(3000)

        total_pages = self._get_total_pages(page)
        page_images = []

        for page_num in range(1, total_pages + 1):
            if page_num > 1:
                self._navigate_to_page(page, page_num)

            img_bytes = self._capture_canvas(page, "[data-testid='preview-canvas-primary']")
            page_images.append(img_bytes)

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
            # format is "1 / 2"
            parts = text.strip().split("/")
            if len(parts) == 2:
                return int(parts[1].strip())
        except Exception:
            pass
        return 1

    def _navigate_to_page(self, page, page_num: int) -> None:
        for _ in range(page_num - 1):
            page.click("[data-testid='preview-next-page-button']")
            page.wait_for_timeout(2500)

    # UI elements that overlap the canvas and must be hidden during capture
    _OVERLAY_SELECTORS = [
        "[data-testid='preview-pagination-container']",
        "[data-testid='preview-customize-button-container']",
    ]

    def _capture_canvas(self, page, selector: str) -> bytes:
        element = page.query_selector(selector)
        if not element:
            raise HTTPException(status_code=500, detail="Failed to capture canvas — resume may not have loaded")

        page.evaluate(
            """(selectors) => selectors.forEach(s => {
                const el = document.querySelector(s);
                if (el) el.style.visibility = 'hidden';
            })""",
            self._OVERLAY_SELECTORS,
        )
        try:
            return element.screenshot(type="png")
        finally:
            page.evaluate(
                """(selectors) => selectors.forEach(s => {
                    const el = document.querySelector(s);
                    if (el) el.style.visibility = '';
                })""",
                self._OVERLAY_SELECTORS,
            )

    def _build_pdf(self, page_images: list[bytes]) -> bytes:
        from pypdf import PdfReader

        pdf_writer = PdfWriter()

        for img_bytes in page_images:
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            pdf_buf = io.BytesIO()
            img.save(pdf_buf, format="PDF", resolution=300)
            pdf_buf.seek(0)

            reader = PdfReader(pdf_buf)
            pdf_writer.add_page(reader.pages[0])

        out = io.BytesIO()
        pdf_writer.write(out)
        return out.getvalue()
