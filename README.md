# resume2io-download

Download your [resume.io](https://resume.io) resume as a PDF — **works on free accounts**.

resume.io locks PDF export behind a paid plan. This tool uses a headless browser to load
your resume editor, captures each page from the canvas, and assembles a clean PDF —
no subscription required.

---

## How it works

1. Launches headless Chromium via Playwright
2. Injects your session cookie to authenticate as you
3. Loads the resume editor and waits for the canvas to fully render
4. Captures each page (hiding UI overlays during capture)
5. Assembles all pages into a single PDF

---

## Quick start (Docker)

```bash
git clone https://github.com/YOUR_USERNAME/resume2io-download.git
cd resume2io-download
docker build -t resume2io-download .
docker run -p 8000:8000 resume2io-download
```

Then open **http://localhost:8000** in your browser.

---

## Step-by-step: how to download your resume

### Step 1 — Find your Resume ID

Open your resume in the editor. The ID is in the URL:

```
https://resume.io/app/resumes/69570346/edit
                              ^^^^^^^^
                              this is your Resume ID
```

### Step 2 — Get your session cookie

You need the `_session_id` cookie from your logged-in browser session.

**Chrome / Edge:**
1. Go to [resume.io](https://resume.io) and make sure you are logged in
2. Open DevTools: press `F12` or right-click → Inspect
3. Click the **Application** tab
4. In the left sidebar expand **Cookies** → click `https://resume.io`
5. Find the row named `_session_id` and copy the **Value** column

**Firefox:**
1. Open DevTools → **Storage** tab
2. Expand **Cookies** → `https://resume.io`
3. Copy the value of `_session_id`

> The session cookie expires when you log out or after ~30 days.
> If the download fails with a 401 error, log in again and repeat this step.

### Step 3 — Download

1. Open **http://localhost:8000**
2. Paste your **Resume ID** (numbers only, e.g. `69570346`)
3. Paste your **`_session_id`** cookie value
4. Click **Download PDF**

The browser will download `{resume_id}.pdf` once rendering is complete (usually 15–30 seconds).

---

## API usage (curl)

```bash
curl -X POST "http://localhost:8000/download/69570346" \
  -H "X-Session-Id: YOUR_SESSION_ID_VALUE" \
  -o my_resume.pdf
```

---

## Running without Docker

Requires Python 3.12+ and [uv](https://github.com/astral-sh/uv).

```bash
uv sync
python -m playwright install chromium
python app/main.py
```

---

## Disclaimer

This tool is for personal use only — to download your own resume.
By using it you agree to comply with resume.io's terms of service.
